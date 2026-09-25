#!/usr/bin/env python3
import argparse
import os
import sys
from google import genai

def main():
    parser = argparse.ArgumentParser(
        description="List all available Gemini models for your API key."
    )
    parser.add_argument(
        "--api-key",
        required=False,
        help="Google API key (optional if GOOGLE_API_KEY env var is set)"
    )
    args = parser.parse_args()

    # 1. Load API Key
    api_key = args.api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        try:
            api_key = input("🔑 Google API Key not found. Please paste it here: ").strip()
        except KeyboardInterrupt:
            sys.exit(1)

        if not api_key:
            sys.stderr.write("Error: API Key is required to check available models.\n")
            sys.exit(1)

    print("⏳ Connecting to Google GenAI to retrieve your models...\n")

    try:
        client = genai.Client(api_key=api_key)

        # 2. Fetch and filter models
        available_models = []
        for model in client.models.list():
            # In the new SDK, we check 'supported_actions' instead of 'supported_generation_methods'
            if "generateContent" in model.supported_actions:
                # Strip the "models/" prefix to give you the exact string to use in your script
                clean_name = model.name.replace("models/", "")
                available_models.append(clean_name)

        # 3. Print the results nicely
        print("✅ Models available for generation:")
        print("--------------------------------------------------")

        # Sort alphabetically so Pro and Flash models group together
        for model_name in sorted(available_models):
            if "pro" in model_name.lower():
                print(f"🌟 {model_name}")
            elif "flash" in model_name.lower():
                print(f"⚡ {model_name}")
            else:
                print(f"   {model_name}")

        print("--------------------------------------------------")
        print(f"Total generation models found: {len(available_models)}")

    except Exception as e:
        sys.stderr.write(f"\n❌ Error fetching models: {e}\n")
        sys.stderr.write("Please check if your API key is valid.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
