import requests
from monnify.monnify import Monnify
from base64 import b64encode
import base64
import os
from datetime import datetime






api_key = os.environ.get("Mon_Api_key")
secret_key = os.environ.get("Mon_Secret_key")
contract_code = os.environ.get("Contract_Code")


# monn = Monnify(api_key, secret_key)

# monn.generateToken()


# data = f"{api_key}:{secret_key}".encode()
# userAndPass = b64encode(data).decode("ascii")

# credentials = f"{api_key}:{secret_key}"
# encoded_string = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

# user_data = base64(f"{api_key}:{secret_key}").en

# print(userAndPass, user_data)

import json

expiryDate = datetime.now()
formatted_date = expiryDate.strftime("%Y-%m-%d %H:%M:%S")

# print(formatted_date)

response = requests.post(
    "https://sandbox.monnify.com/api/v1/auth/login",
    headers={
      "Authorization": "Basic TUtfVEVTVF9HQzNCOFhHMlhYOkE2NjNOUlpBNTQ0RERQRU03S0RON1o4SFJWNllYRDhT"
    }
)

data = json.loads(response.content)

accessToken = str(data['responseBody']['accessToken'])




# response = requests.post(
#     "https://sandbox.monnify.com/api/v1/auth/login",
#     headers={
#       "Authorization": f"Basic {encoded_string}"
#     }
# )

# print(response)



response = requests.post(
    "https://sandbox.monnify.com/api/v1/vas/nin-details",
    headers={
      "Authorization": f"Bearer {accessToken}",
      "Content-Type": "application/json"
    },
    json={
      "nin": "94646622685"
    }
)





# response = requests.post(
#     "https://sandbox.monnify.com/api/v1/invoice/create",
#     headers={
#       "Authorization": "Bearer <token>",
#       "Content-Type": "application/json"
#     },
#     json={
#       "amount": 999,
#       "currencyCode": "NGN",
#       "invoiceReference": "183891300182",
#       "customerName": "John Snow",
#       "customerEmail": "johnsnow@gmail.com",
#       "contractCode": "7059707855",
#       "description": "test invoice",
#       "expiryDate": "2022-10-30 12:00:00",
#       "paymentMethods": [],
#     #   "incomeSplitConfig": [
#     #     {
#     #       "subAccountCode": "MFY_SUB_319452883228",
#     #       "feePercentage": 10.5,
#     #       "splitPercentage": 20,
#     #       "feeBearer": true
#     #     }
#     #   ],
#       "redirectUrl": "http://app.monnify.com",
#       "accountReference": ""
#     }
# )

print(response.content)