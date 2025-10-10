#!/usr/bin/env python3
import argparse
from google import genai
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Run an agent on Gemini 2.5 Flash with enclosed files.")
    parser.add_argument("--api-key", required=False, help="Google API key for Gemini access")
    parser.add_argument("--agent-setup", required=True, help="Path to a file containing the agent's instructions")
    parser.add_argument("--input", required=False, help="Comma-separated list of paths of files to enclose to the agent")
    parser.add_argument("--dump-to", required=True, help="Path to output file")
    args = parser.parse_args()

    # Load API key (optional fallback)
    if not args.api_key:
        try:
            default_key = os.environ.get("GOOGLE_API_KEY")
            if not default_key:
                raise ValueError("No API key provided and GOOGLE_API_KEY not set in environment.")
            args.api_key = default_key
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)

    # Read agent instructions
    if not os.path.exists(args.agent_setup):
        sys.stderr.write(f"Error: instructions file not found: {args.agent_setup}:n")
        sys.exit(1)

    with open(args.agent_setup, "r", encoding="utf-8") as f:
        agent_instructions = f.read().strip()

    # Collect attached contents
    enclosed_contents = []
    if args.input:
        paths = [p.strip() for p in args.input.split(",") if p.strip()]
        for path in paths:
            if not os.path.exists(path):
                sys.stderr.write(f"Warning: enclosed file not found: {path}\n")
                continue
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                enclosed_contents.append({"path": path, "content": content})

    # Build full prompt
    combined_prompt = agent_instructions
    if enclosed_contents:
        combined_prompt += "\n\n### ENCLOSED FILES ###\n"
        for file in enclosed_contents:
            combined_prompt += f"\n# {file['path']}\n{file['content']}\n"

    # ---- Prompt length check ----
    MAX_TOKENS = 1_000_000            # Approx Gemini 2.5 Flash context window
    AVG_CHARS_PER_TOKEN = 4
    MAX_CHARS = MAX_TOKENS * AVG_CHARS_PER_TOKEN

    if len(combined_prompt) > MAX_CHARS:
        sys.stderr.write(
            f"Error: prompt too long ({len(combined_prompt):,} chars, "
            f"limit ≈ {MAX_CHARS:,}).\n"
            "Consider shortening the instructions or enclosing fewer/lighter files.\n"
        )
        sys.exit(1)
    # ------------------------------

    # Send to model
    try:
        print("⏳ Querying Gemini 2.5 Flash...")
        client = genai.Client(api_key=args.api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=combined_prompt
        )
        output = response.text
    except Exception as e:
        sys.stderr.write(f"Error while querying Gemini: {e}\n")
        sys.exit(1)

    # Write output
    try:
        with open(args.dump_to, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ Output written to {args.dump_to}")
    except Exception as e:
        sys.stderr.write(f"Error writing output: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

