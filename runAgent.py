#!/usr/bin/env python3
import argparse
from google import genai
import sys
import os
import time

# --- Configuration & Limits ---
# Strict limit based on your Free Tier TPM stats
HARD_TOKEN_LIMIT = 250_000
MAX_UPLOAD_FILES = 10


def main():
    parser = argparse.ArgumentParser(
        description="Run an agent on Gemini 2.5 Flash with enclosed files."
    )
    parser.add_argument("--api-key", required=False, help="Google API key")
    parser.add_argument(
        "--agent-setup", required=True, help="Path to instructions"
    )
    parser.add_argument(
        "--enclose-files-as-prompt", default="", help="Text files to append"
    )
    parser.add_argument(
        "--enclose-files", default="", help="Files to upload (PDF/Images)"
    )
    parser.add_argument(
        "--print-prompt-only", action="store_true", help="Debug mode"
    )
    parser.add_argument("--dump-to", required=True, help="Output file path")
    args = parser.parse_args()

    # 1. Load API Key
    api_key = args.api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        sys.stderr.write("Error: API Key not found.\n")
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
        print("🔍 Validating token count...")
        # Using gemini-2.0-flash as the stable ID for 2.5 flash behaviors
        count = client.models.count_tokens(
            model="gemini-2.5-flash", contents=generation_contents
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

    # 6. Execute Query
    try:
        print("⏳ Querying Gemini 2.5 Flash...")
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=generation_contents
        )
        print("✅ Query successful.")
        with open(args.dump_to, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✅ Output written to {args.dump_to}")
    except Exception as e:
        sys.stderr.write(f"❌ Error during generation: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
