import requests
import os
import paystack

url = "https://api.flutterwave.com/v3/payment-plans"
secret_key = os.environ.get("FLUTTERWAVE_SECRET_KEY")

payload = {
    "amount": 5000,
    "name": "Package 1",
    "interval": "Monthly",
    "duration": 24
}
headers = {
    "Authorization": f"Bearer {secret_key}",
    "Content-Type": "application/json",
    "accept": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.text)