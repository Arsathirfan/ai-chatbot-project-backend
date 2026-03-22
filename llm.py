import requests

API_KEY = "YOUR_GEMINI_API_KEY"

def generate_llm_response(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(response.text)
        raise Exception("LLM API failed")

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Error generating response"