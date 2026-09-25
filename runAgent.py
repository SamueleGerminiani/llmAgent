#!/usr/bin/env python3
import argparse
from google import genai
from google.genai import types
import sys
import os
import time

# --- Configuration & Limits ---
# Strict limit based on your Free Tier TPM stats
HARD_TOKEN_LIMIT = 250_000
MAX_UPLOAD_FILES = 10


def main():
    parser = argparse.ArgumentParser(
        description="Run an agent on Gemini models with enclosed files."
    )
    parser.add_argument("--api-key", required=False, help="Google API key")

    # NEW ARGUMENT FOR MODEL SELECTION
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="The Gemini model to use (default: gemini-2.5-flash)"
    )

    parser.add_argument(
        "--agent-setup", required=True, help="Path to instructions"
    )
    parser.add_argument(
        "--enclose-files-as-prompt",
        default="",
        nargs="?",  # This makes the value optional
        const="",
        help="Text files to append",
    )
    parser.add_argument(
        "--enclose-files",
        default="",
        nargs="?",  # This makes the value optional
        const="",
        help="Files to upload (PDF/Images)",
    )
    parser.add_argument(
        "--print-prompt-only", action="store_true", help="Debug mode"
    )
    parser.add_argument("--dump-to", required=True, help="Output file path")

    # NEW ARGUMENTS FOR TEMPERATURE AND SEED
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for the LLM (default: 0.7)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Integer seed for reproducible generation"
    )

    args = parser.parse_args()

    # 1. Load API Key (with interactive fallback)
    api_key = args.api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        try:
            api_key = input("🔑 Google API Key not found. Please paste it here: ").strip()
        except KeyboardInterrupt:
            sys.exit(1)

        if not api_key:
            sys.stderr.write("Error: API Key is required.\n")
            sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 2. Read Agent Instructions
    if not os.path.exists(args.agent_setup):
        sys.stderr.write(
            f"Error: Instructions file not found: {args.agent_setup}\n"
        )
        sys.exit(1)

    with open(args.agent_setup, "r", encoding="utf-8") as f:
        combined_text_prompt = f.read().strip()

    # 3. Process Text Files (Append to prompt)
    if args.enclose_files_as_prompt:
        paths = [
            p.strip()
            for p in args.enclose_files_as_prompt.split(",")
            if p.strip()
        ]
        for path in paths:
            if not os.path.exists(path):
                sys.stderr.write(f"Error: Text file not found: {path}\n")
                sys.exit(1)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    combined_text_prompt += f"\n# FILE: {path}\n{f.read()}\n"
            except Exception as e:
                sys.stderr.write(f"Error reading {path}: {e}\n")
                sys.exit(1)

    # 4. Process API Uploads
    uploaded_file_objects = []
    if args.enclose_files:
        paths = [p.strip() for p in args.enclose_files.split(",") if p.strip()]
        if len(paths) > MAX_UPLOAD_FILES:
            sys.stderr.write(
                f"Error: Too many files ({len(paths)}). Limit is {MAX_UPLOAD_FILES}.\n"
            )
            sys.exit(1)

        print(f"⏳ Uploading {len(paths)} file(s)...")
        for path in paths:
            if not os.path.exists(path):
                sys.stderr.write(f"Error: File not found: {path}\n")
                sys.exit(1)
            try:
                uploaded_file = client.files.upload(file=path)
                print(
                    f"   Ref: {uploaded_file.name} | State: {uploaded_file.state}"
                )

                while uploaded_file.state == "PROCESSING":
                    time.sleep(1)
                    uploaded_file = client.files.get(name=uploaded_file.name)

                if uploaded_file.state == "FAILED":
                    raise ValueError(f"Processing failed for {path}")
                uploaded_file_objects.append(uploaded_file)
            except Exception as e:
                sys.stderr.write(f"Error uploading {path}: {e}\n")
                sys.exit(1)

    # 5. Token Guard Check
    generation_contents = [combined_text_prompt] + uploaded_file_objects

    if args.print_prompt_only:
        print("=== Text Prompt ===\n", combined_text_prompt)
        sys.exit(0)

    try:
        print(f"🔍 Validating token count for {args.model}...")
        # Use dynamic model argument for counting tokens
        count = client.models.count_tokens(
            model=args.model, contents=generation_contents
        )
        total_tokens = count.total_tokens

        if total_tokens > HARD_TOKEN_LIMIT:
            sys.stderr.write(
                f"❌ LIMIT EXCEEDED: Input is {total_tokens:,} tokens.\n"
            )
            sys.stderr.write(
                f"   Your limit is {HARD_TOKEN_LIMIT:,} (Free Tier).\n"
            )
            sys.exit(1)

        print(f"✅ Context safe: {total_tokens:,} tokens.")
    except Exception as e:
        sys.stderr.write(
            f"Warning: Token validation failed ({e}). Proceeding carefully...\n"
        )

    # 6. Execute Query with Retry Logic
    print(f"⏳ Querying {args.model} (Temp: {args.temperature}, Seed: {args.seed})...")

    # Configure Generation settings (Temperature & Seed)
    config_kwargs = {"temperature": args.temperature}
    if args.seed is not None:
        config_kwargs["seed"] = args.seed

    generation_config = types.GenerateContentConfig(**config_kwargs)

    retry_delay = 10  # Start with a 10-second delay

    while True:
        try:
            # Use dynamic model argument for generating content
            response = client.models.generate_content(
                model=args.model,
                contents=generation_contents,
                config=generation_config
            )
            print("✅ Query successful.")
            with open(args.dump_to, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"✅ Output written to {args.dump_to}")
            break  # Exit the while loop if generation was successful

        except Exception as e:
            error_message = str(e)
            # Check specifically for the 503 UNAVAILABLE status
            if "503" in error_message and "UNAVAILABLE" in error_message:
                print(f"⚠️ Model experiencing high demand (503). Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Optional: Increase the delay slightly each time to prevent hammering the API (capped at 60s)
                retry_delay = min(retry_delay + 5, 60)
            else:
                # If it's a different error (e.g., 400 Bad Request), fail immediately
                sys.stderr.write(f"❌ Error during generation: {e}\n")
                sys.exit(1)


if __name__ == "__main__":
    main()
