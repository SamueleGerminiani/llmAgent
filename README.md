# llmAgent — Command-Line Interface for Gemini 2.5 Flash

**llmAgent** is a simple Python command-line tool to query **Google’s Gemini 2.5 Flash** model using the **`google-genai`** SDK.  
It allows you to send a prompt directly via `--prompt` or read it from a text file via `--input`, and save the model’s response to a specified output file.

---

## 🧩 Features

- Query **Gemini 2.5 Flash** directly from the terminal  
- Accepts inline prompts (`--prompt`) or file-based input (`--input`)  
- Dumps results to a file (`--dump-to`)  
- Graceful error handling and minimal dependencies  

---

## ⚙️ Requirements

- **Python 3.8+**  
- The [`google-genai`](https://pypi.org/project/google-genai/) package  
- A **Google API key** with access to Gemini models  

---

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llmAgent.git
   cd llmAgent
   ```

2. Install dependencies:
   ```bash
   pip install google-genai
   ```

3. Make the script executable (optional):
   ```bash
   chmod +x runAgent.py
   ```

---

## 🚀 Usage

### 1. With an inline prompt

```bash
./runAgent.py \
  --api-key "YOUR_API_KEY" \
  --prompt "Explain quantum computing in simple terms." \
  --dump-to output.txt
```

### 2. With a prompt file

```bash
./runAgent.py \
  --api-key "YOUR_API_KEY" \
  --input prompt.txt \
  --dump-to output.txt
```

### 3. Example output

```bash
✅ Output written to output.txt
```

---

## 🧠 Arguments

| Argument       | Required | Description |
|----------------|-----------|-------------|
| `--api-key`    | ✅*       | Google API key for Gemini access. If omitted, the script will look for a `default_key` variable (not recommended). |
| `--prompt`     | No        | Prompt text to send to the model. |
| `--input`      | No        | Path to a text file containing the prompt. |
| `--dump-to`    | ✅        | Path where the model’s response will be saved. |

> **Note:** Either `--prompt` or `--input` must be provided.

---

## ⚠️ Error Handling

- If both `--prompt` and `--input` are missing → script exits with an error  
- If the input file does not exist → script exits with an error  
- API or network errors → printed to `stderr` with an error message  

---

## 🧰 Example Workflow

```bash
echo "Write a haiku about machine learning." > prompt.txt

./runAgent.py \
  --api-key "AIza..." \
  --input prompt.txt \
  --dump-to result.txt

cat result.txt
```

Output:
```
Neural roots take form,
Learning deep within the code,
Patterns bloom anew.
```

---

