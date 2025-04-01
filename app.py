import os
import uuid
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import stripe

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB setup
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Gemini config
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# OpenAI config
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Stripe config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ====== MODELS ======
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    subscribed = db.Column(db.Boolean, default=False)
    stripe_customer_id = db.Column(db.String(120), unique=True, nullable=True)

class GeneratedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ====== HELPERS ======
def save_binary_file(file_name, data):
    full_path = os.path.join("static", file_name)
    with open(full_path, "wb") as f:
        f.write(data)

def enhance_prompt_with_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    full_prompt = (
        "You are an expert in crafting prompts specifically for DALL·E image generation. "
        "Your task is to enhance the following input prompt while preserving its core idea. "
        "Make the result vivid, emotionally engaging, and visually detailed. "
        "Ensure strong composition, realistic lighting, and atmospheric depth. "
        "Avoid adding excessive objects unless explicitly stated. "
        "Keep the final prompt concise and under 1000 characters. "
        f"Input prompt: {prompt}"
    )

    try:
        response = model.generate_content(full_prompt)
        enhanced = response.text.strip()
        return enhanced[:997] + "..." if len(enhanced) > 1000 else enhanced
    except Exception as e:
        print(f"Gemini error: {e}")
        return prompt

def generate_image_with_openai(prompt):
    try:
        # Try DALL-E 3 first
        try_model = "dall-e-3"
        response = client.images.generate(
            model=try_model,
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
    except Exception as e:
        print(f"⚠️ Failed with {try_model}, trying dall-e-2. Error: {e}")
        try_model = "dall-e-2"
        response = client.images.generate(
            model=try_model,
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )

    if not response.data:
        return {"status": "text", "message": f"No image returned from OpenAI ({try_model})."}

    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    file_name = f"{uuid.uuid4()}.png"
    save_binary_file(file_name, image_data)
    return {"status": "image", "file_name": file_name}

# ====== ROUTES ======
@app.route('/')
@login_required
def index():
    return render_template('index.html', user_email=current_user.email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed = generate_password_hash(password)
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
        else:
            user = User(email=email, password=hashed)
            db.session.add(user)
            db.session.commit()
            flash('Account created, please log in')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/generate-image', methods=['POST'])
@login_required
def generate_image():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    enhanced = enhance_prompt_with_gemini(prompt)
    result = generate_image_with_openai(enhanced)
    if result["status"] == "image":
        return jsonify({"imageUrl": f"/static/{result['file_name']}"})
    else:
        return jsonify({"error": result.get("message", "Image generation failed.")}), 400

@app.route('/api/check-subscription', methods=['GET'])
@login_required
def check_subscription():
    return jsonify({"subscribed": current_user.subscribed})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/api/subscribe', methods=['POST'])
@login_required
def subscribe():
    user = current_user
    try:
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email)
            user.stripe_customer_id = customer.id
            db.session.commit()
        else:
            customer = stripe.Customer.retrieve(user.stripe_customer_id)

        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': os.getenv('STRIPE_PRICE_ID'),
                'quantity': 1,
            }],
            success_url='http://localhost:5000/?subscribed=true',
            cancel_url='http://localhost:5000/?canceled=true',
        )
        return jsonify({'checkoutUrl': session.url})
    except Exception as e:
        print("Stripe error:", e)
        return jsonify({"error": str(e)}), 400

@app.route('/webhook', methods=['POST'])
def webhook_received():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except Exception as e:
        return jsonify(success=False, error=str(e)), 400

    if event['type'] == 'checkout.session.completed':
        print("✅ Received checkout.session.completed")
        session_data = event['data']['object']
        customer_id = session_data.get('customer')
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            user.subscribed = True
            db.session.commit()
            print(f"✅ Subscription activated for {user.email}")
        else:
            print("❌ No user matched the customer ID")
    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(debug=True)
