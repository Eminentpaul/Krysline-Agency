import requests
from monnify.monnify import Monnify
from base64 import b64encode
import os
import json
from datetime import datetime
# from .bank_codes import bank_codes_name



# Bank names and it's codes 
bank_codes_name = [
    ('044-Access Bank', 'Access Bank'),
    ('063-Access Bank (Diamond)', 'Access Bank (Diamond)'),
    ('070-Fidelity Bank', 'Fidelity Bank'),
    ('011-First Bank of Nigeria', 'First Bank'),
    ('214-First City Monument Bank', 'FCMB'),
    ('058-Guaranty Trust Bank', 'GTB'),
    ('50515-Moniepoint MFB', 'Moniepoint MFB'),
    ('999992-OPay Digital Services Limited (OPay)', 'OPay'),
    ('232-Sterling Bank', 'Sterling Bank'),
    ('033-United Bank For Africa', 'UBA'),
    ('035-Wema Bank', 'Wema Bank'),
    ('057-Zenith Bank', 'Zenith Bank'),
]



# MONNIFY AUTHENTICATION
api_key = os.environ.get("Mon_Api_key")
secret_key = os.environ.get("Mon_Secret_key")
contract_code = os.environ.get("Contract_Code")


# BaseUrls
base_url="https://api.monnify.com"

data = f"{api_key}:{secret_key}".encode()
apKey_Secret = b64encode(data).decode("ascii")


def access_token(apKeySecretKey):
    response = requests.post(
        f"{base_url}/api/v1/auth/login",
        headers={
        "Authorization": f"Basic {apKeySecretKey}"
        }
    )

    data = json.loads(response.content)

    accessToken = str(data['responseBody']['accessToken'])

    return accessToken





accessTonken=access_token(apKey_Secret)

headers={
      "Authorization": f"Bearer {accessTonken}",
      "Content-Type": "application/json"
    }






def get_bank_code(bank_name: str, codelist=bank_codes_name):

    bank_name = bank_name.split("-")[1]
    
    for bank in codelist:
        code, bankName = bank[0].split("-")

        if bank_name == str(bankName):
            return code
    else:
        return ValueError




# admin_bank_name = str(os.environ.get('bankName'))
admin_account_number = os.environ.get("accountNumber")



def bank_verification(accountNumber, bankName):
    accountNumber = str(accountNumber)
    bankCode = get_bank_code(bank_name=bankName)

    
    response = requests.get(
        f"{base_url}/api/v1/disbursements/account/validate",
        headers=headers,

        params={
        "accountNumber": accountNumber,
        "bankCode": bankCode
        }
    )

    data = json.loads(response.content) 
 
    if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
        return data['responseBody'], True
    else:
        return data['responseMessage'], False
    



def maskAccountNumber(number):
    pre = str(number)[:3]
    post = str(number)[-3:]

    return str(f"{pre}****{post}")






def create_invoice(amount, user, description, reference, expirydate):

        response = requests.post(
                    f"{base_url}/api/v1/invoice/create",
                    headers=headers,
                    json={
                    "amount": amount,
                    "currencyCode": "NGN",
                    "invoiceReference": reference,
                    "customerName": user.get_full_name(),
                    "customerEmail": user.email,
                    "contractCode": contract_code,
                    "description": description,
                    "expiryDate": expirydate,
                    
                    "redirectUrl": "https://royal-dilemmatical-tartishly.ngrok-free.dev/Dashboard/payments/",
                    "accountReference": ""
                    }
                )
        data = json.loads(response.content)
        print(data)
        if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
            return data['responseBody'], True
        else:
            return data['responseMessage'], False



def get_invoice(reference):
    response = requests.get(
            f"{base_url}/api/v1/invoice/{reference}/details",
            headers={
            "Authorization": f"Bearer {accessTonken}"
            }
        )
    
    data = json.loads(response.content)

    print("Get Invoice: ", data)

    if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
        return data['responseBody'], True
    else:
        return data['responseMessage'], False




def cancle_invoice(reference):
    response = requests.delete(
            f"{base_url}/api/v1/invoice/{reference}/cancel",
            headers={
            "Authorization": f"Bearer {accessTonken}"
            }
        )
    
    data = json.loads(response.content)
    print("Cancle: ", data)

    if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
        return data['responseBody'], True
    else:
        return data['responseMessage'], False




# def get_transaction(reference):
#     response = requests.get(
#             f"{base_url}/api/v2/transactions/{reference}",
#             headers={
#             "Authorization": f"Bearer {accessTonken}"
#             }
#         )
    
#     data = json.loads(response.content)

#     if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
#         return data['responseBody'], True
#     else:
#         return data['responseMessage'], False



def initiate_transdfer(accountNumber, bankName):

    # {'accountNumber': '0570385531', 'accountName': 'OSHI PAULINUS OFFORBUIKE', 'bankCode': '058', 'currencyCode': 'NGN'}

    # Setting the banks accounts 
    # admin_bank = bank_verification(admin_account_number, admin_bank_name)
    destinationDetails, valid = bank_verification(accountNumber, bankName)

    if valid:
        bcode = str(destinationDetails['bankCode'])
        anumber = str(destinationDetails['accountNumber'])
        cname = str(destinationDetails['accountName'])



        response = requests.post(
                f"{base_url}/api/v2/disbursements/single",
                headers=headers,
                json={
                "amount": 200,
                "reference": "reference---1290034",
                "narration": "911 Transaction",
                "destinationBankCode": "50515",
                "destinationAccountNumber": "2085886393",
                "currency": "NGN",
                "sourceAccountNumber": "3934178936",
                "senderInfo": {
                    "sourceAccountNumber": "3934178936",
                    "sourceAccountName": "Marvelous Benji",
                    "sourceAccountBvn": "1234567890",
                    "senderBankCode": "50515"
                },
                # "async": false
                }
            )
        
        print(response)
        data = json.loads(response.content)
        print(data)







def transfer():
    response = requests.post(
        "https://sandbox.monnify.com/api/v2/disbursements/single/validate-otp",
        headers,
        json={
        "reference": "refere--n00ce---1290034",
        "authorizationCode": "491763"
        }
    )
