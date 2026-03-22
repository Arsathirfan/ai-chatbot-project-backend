import requests

API_KEY = "YOUR_GEMINI_API_KEY"

def get_embedding(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={API_KEY}"

    payload = {
        "content": {
            "parts": [{"text": text}]
        }
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(response.text)
        raise Exception("Embedding API failed")

    return response.json()["embedding"]["values"]