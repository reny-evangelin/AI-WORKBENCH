import requests

try:
    print("Testing /chat...")
    res = requests.post("http://127.0.0.1:8000/chat", data={"message": "test"})
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
