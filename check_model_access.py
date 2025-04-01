from openai import OpenAI
import os

# Set your API key here or pull from your .env
API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=API_KEY)

def check_model_access(target_model="dall-e-3"):
    try:
        print("🔍 Fetching available models...")
        models = client.models.list()
        model_ids = [model.id for model in models.data]

        print("\n🧠 Models accessible with your API key:")
        for mid in sorted(model_ids):
            print(" -", mid)

        print("\n🚦 Access Check:")
        if target_model in model_ids:
            print(f"✅ You DO have access to '{target_model}'")
        else:
            print(f"❌ You do NOT have access to '{target_model}'")

    except Exception as e:
        print("❌ Error while checking models:", e)

if __name__ == "__main__":
    check_model_access()
