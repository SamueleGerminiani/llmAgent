#!/usr/bin/env python3
import argparse
from google import genai
from google.genai import types
import sys
import os
import time

# --- Configuration & Limits ---
MAX_TEXT_TOKENS = 1_000_000  # Approx context window for Gemini
AVG_CHARS_PER_TOKEN = 4
MAX_CHARS = MAX_TEXT_TOKENS * AVG_CHARS_PER_TOKEN
MAX_UPLOAD_FILES = 10  # Soft limit to prevent spamming uploads in one go


def main():
    parser = argparse.ArgumentParser(
        description="Run an agent on Gemini 2.5 Flash with enclosed files."
    )
    parser.add_argument(
        "--api-key", required=False, help="Google API key for Gemini access"
    )
    parser.add_argument(
        "--agent-setup",
        required=True,
        help="Path to a file containing the agent's instructions",
    )
    # Option 1: Read file and append text to prompt
    parser.add_argument(
        "--enclose-files-as-prompt",
        required=False,
        nargs='?',
        const="",
        default="",
        help="Comma-separated list of text files to read and append to the prompt",
    )
    # Option 2: Upload file using API
    parser.add_argument(
        "--enclose-files",
        required=False,
        nargs='?',
        const="",
        default="",
        help="Comma-separated list of files (PDF, Images, etc.) to upload via File API",
    )

    parser.add_argument(
        "--print-prompt-only",
        required=False,
        help="If used, the script will only print the constructed prompt and exit without querying the model. Useful for debugging.",
        action="store_true",
    )
    parser.add_argument("--dump-to", required=True, help="Path to output file")
    args = parser.parse_args()

    # 1. Load API Key
    if not args.api_key:
        try:
            default_key = os.environ.get("GOOGLE_API_KEY")
            if not default_key:
                raise ValueError(
                    "No API key provided and GOOGLE_API_KEY not set in environment."
                )
            args.api_key = default_key
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)

    # Initialize Client
    client = genai.Client(api_key=args.api_key)

    # 2. Read Agent Instructions
    if not os.path.exists(args.agent_setup):
        sys.stderr.write(
            f"Error: instructions file not found: {args.agent_setup}\n"
        )
        sys.exit(1)

    with open(args.agent_setup, "r", encoding="utf-8") as f:
        agent_instructions = f.read().strip()

    # 3. Process --enclose-files-as-prompt (Text Append)
    text_prompt_files = []
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
                    content = f.read()
                    text_prompt_files.append(
                        {"path": path, "content": content}
                    )
            except Exception as e:
                sys.stderr.write(f"Error reading {path}: {e}\n")
                sys.exit(1)

    # Construct the text portion of the prompt
    combined_text_prompt = agent_instructions
    if text_prompt_files:
        for file in text_prompt_files:
            combined_text_prompt += f"\n# {file['path']}\n{file['content']}\n"

    # Check Text Size Limits
    if len(combined_text_prompt) > MAX_CHARS:
        sys.stderr.write(
            f"Error: Text prompt size ({len(combined_text_prompt):,} chars) "
            f"exceeds safe limit (~{MAX_CHARS:,} chars).\n"
        )
        sys.exit(1)

    # 4. Process --enclose-files (API Upload)
    uploaded_file_objects = []
    if args.enclose_files:
        paths = [p.strip() for p in args.enclose_files.split(",") if p.strip()]

        if len(paths) > MAX_UPLOAD_FILES:
            sys.stderr.write(
                f"Error: Too many files to upload ({len(paths)}). Limit is {MAX_UPLOAD_FILES}.\n"
            )
            sys.exit(1)

        print(f"⏳ Uploading {len(paths)} file(s) to Google GenAI...")

        for path in paths:
            if not os.path.exists(path):
                sys.stderr.write(f"Error: File to upload not found: {path}\n")
                sys.exit(1)

            try:
                # Use the 'file' argument instead of 'path'
                uploaded_file = client.files.upload(file=path)
                print(
                    f"   Ref: {uploaded_file.name} | State: {uploaded_file.state}"
                )

                # Check for active state
                while uploaded_file.state == "PROCESSING":
                    print(f"   Waiting for {path} to process...")
                    time.sleep(1)
                    uploaded_file = client.files.get(name=uploaded_file.name)

                if uploaded_file.state == "FAILED":
                    raise ValueError(f"File processing failed for {path}")

                uploaded_file_objects.append(uploaded_file)

            except Exception as e:
                sys.stderr.write(f"Error uploading {path}: {e}\n")
                sys.exit(1)

    # 5. Prepare Content for Generation
    # content list: [text_prompt, file_obj1, file_obj2, ...]
    generation_contents = [combined_text_prompt]
    generation_contents.extend(uploaded_file_objects)

    if args.print_prompt_only:
        print("=== Constructed Prompt & File References ===")
        print(combined_text_prompt)
        if uploaded_file_objects:
            print("\n=== Uploaded Files ===")
            for f in uploaded_file_objects:
                print(f)
        print("=== End of Prompt & File References ===")
        sys.exit(0)

    # 6. Send to Model
    try:
        print("⏳ Querying Gemini 2.5 Flash...")
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=generation_contents
        )
        output = response.text
        print("✅ Query successful.")
        print("--- Output Start ---")
        print(output)
        print("--- Output End ---")
    except Exception as e:
        sys.stderr.write(f"Error while querying Gemini: {e}\n")
        sys.exit(1)

    # 7. Write Output
    try:
        with open(args.dump_to, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ Output written to {args.dump_to}")
    except Exception as e:
        sys.stderr.write(f"Error writing output: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
