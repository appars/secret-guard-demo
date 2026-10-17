"""✅ GOOD PRACTICE: API key read from the environment and validated before use."""

import json
import os
import ssl
import sys
import urllib.error
import urllib.request

BASE_URL = "https://api.groq.com/openai/v1"

# Known chat models, in order of preference (pinned, not guessed)
PREFERRED_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]

# Use certifi's certificates if installed (avoids SSL errors on some Macs)
try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()


def call_groq(path, key, body=None):
    """Call the Groq API. Returns (status_code, json_or_error_text)."""
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body).encode() if body else None,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "secret-guard-demo/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except urllib.error.URLError as e:
        return 0, f"Network error: {e.reason}"


def validate_key():
    """Validate the token in 3 steps and return (key, model)."""
    # Step 1: the key must come from the environment, not the code
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        sys.exit("❌ Step 1: GROQ_API_KEY not set.\n   Run: export GROQ_API_KEY='gsk_...'")
    print("🔐 Step 1: Is the key set?               ✅")

    # Step 2: check the format before sending it anywhere
    if not key.startswith("gsk_"):
        sys.exit("❌ Step 2: This does not look like a Groq key (must start with gsk_).")
    print("🔐 Step 2: Does it look like a Groq key? ✅")

    # Step 3: ask Groq if the key is valid (list available models)
    status, data = call_groq("/models", key)
    if status == 401:
        sys.exit("❌ Step 3: Groq rejected the key (invalid or revoked).")
    if status != 200:
        sys.exit(f"❌ Step 3: Could not reach Groq → {status}: {data}")

    # Use the first preferred chat model this key has access to
    available = {m["id"] for m in data["data"]}
    chat = [m for m in PREFERRED_MODELS if m in available]
    if not chat:
        sys.exit("❌ Step 3: No known chat model available for this key.")
    print(f"🔐 Step 3: Does Groq accept it?          ✅  (model: {chat[0]})")
    return key, chat[0]


def ask_groq(key, model, question):
    """Send a question and return the answer text."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a friendly CSE tutor. Answer in 3 lines."},
            {"role": "user", "content": question},
        ],
    }
    status, data = call_groq("/chat/completions", key, body)
    if status != 200:
        return f"❌ Error {status}: {data}"
    return data["choices"][0]["message"]["content"]
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if __name__ == "__main__":
    key, model = validate_key()
    q = input("\n🎓 Ask your doubt: ")
    print("\n🤖", ask_groq(key, model, q))
