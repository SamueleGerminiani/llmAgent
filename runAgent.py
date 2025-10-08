#!/usr/bin/env python3
import argparse
from google import genai
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Query Gemini 2.0 Flash via google-genai SDK.")
    parser.add_argument("--api-key", required=False, help="Google API key for Gemini access")
    parser.add_argument("--prompt", help="Prompt text to send to the model")
    parser.add_argument("--input", help="Path to a text file containing the prompt")
    parser.add_argument("--dump-to", required=True, help="Path to output file")
    args = parser.parse_args()

    if not args.api_key:
        args.api_key = default_key

    # Read prompt
    if args.input:
        if not os.path.exists(args.input):
            sys.stderr.write(f"Error: input file not found: {args.input}\n")
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        sys.stderr.write("Error: You must provide either --prompt or --input\n")
        sys.exit(1)

    try:
        client = genai.Client(api_key=args.api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        output = response.text
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    with open(args.dump_to, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✅ Output written to {args.dump_to}")

if __name__ == "__main__":
    main()

