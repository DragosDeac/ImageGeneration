# DALL·E Image Generation Platform with Stripe Subscriptions

A web application that integrates OpenAI's DALL·E 3 for image generation, along with Stripe for managing transactions and subscriptions.

## Features
- Generate images using OpenAI's DALL·E 3
- User authentication and JWT-based authorization
- Subscription management with Stripe
- Database transactions handled via SQLAlchemy
- Flask-based backend with RESTful APIs
- Dockerized for easy deployment

## Getting Started

### Prerequisites
Ensure you have the following installed:
- Python 3.10+
- Docker & Docker Compose
- OpenAI API Key with DALL·E 3 enabled
- Stripe API Key
- PostgreSQL (optional for local development)

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
   ```
2. Create a virtual environment and install dependencies:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. Set up environment variables (`.env` file):
   ```
   OPENAI_API_KEY=your_openai_api_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

### Running Locally
1. Start the application:
   ```sh
   flask run
   ```
2. Access the API at `http://127.0.0.1:5000`

### Docker Setup
1. Build and run the Docker container:
   ```sh
   docker-compose up --build
   ```
2. The app will be available at `http://localhost:5000`

## API Endpoints

### Generate an Image
```http
POST /api/generate-image
```
**Request:**
```json
{
  "prompt": "A futuristic city skyline at sunset"
}
```
**Response:**
```json
{
  "image_url": "https://generated-image-url.com/image.png"
}
```

### Check Subscription
```http
GET /api/check-subscription
```
**Response:**
```json
{
  "status": "active",
  "plan": "pro"
}
```

## Database Transactions
This project uses SQLAlchemy transactions to ensure consistency. If a transaction fails, it rolls back to maintain data integrity.

```python
try:
    user.balance -= 10  # Deduct from user balance
    db.session.commit()
except Exception:
    db.session.rollback()
```

## Contributing
Contributions are welcome. Please follow these steps:
1. Fork the repository
2. Create a new branch (`feature/your-feature`)
3. Commit your changes
4. Push the branch and open a pull request

Thank you for your time! :)

