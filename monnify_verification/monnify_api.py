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

# admin_bank_name = str(os.environ.get('bankName'))
admin_account_number = os.environ.get("accountNumber")
admin_bank_code = os.environ.get("bankCode")
admin_bank_name = os.environ.get("bankName")
admin_wallet_number = os.environ.get("walletNumber")


# BaseUrls
base_url = "https://api.monnify.com"

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


accessTonken = access_token(apKey_Secret)

headers = {
    "Authorization": f"Bearer {accessTonken}",
    "Content-Type": "application/json"
}


def get_bank_code(bank_name: str, codelist=bank_codes_name):

    bank_map = {}

    for bank in codelist:
        try:
            code, name = bank[0].split('-', 1) 
            bank_map[name.strip()] = code.strip()
        except ValueError:
            continue

    try:
        _, selected_name = bank_name.split('-', 1)
    except ValueError:
        raise ValueError("Invalid bank format")

    return bank_map.get(selected_name.strip())


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


def initiate_transfer(accountNumber, bankName):

    # {'accountNumber': '0570385531', 'accountName': 'OSHI PAULINUS OFFORBUIKE', 'bankCode': '058', 'currencyCode': 'NGN'}

    # Setting the banks accounts
    # admin_bank = bank_verification(admin_account_number, admin_bank_name)
    destinationDetails, dvalid = bank_verification(
        accountNumber=accountNumber, bankName=bankName)
    


    if dvalid:
        bcode = str(destinationDetails['bankCode'])
        anumber = str(destinationDetails['accountNumber'])
        cname = str(destinationDetails['accountName'])

        response = requests.post(
            f"{base_url}/api/v2/disbursements/single",
            headers=headers,
            json={
                "amount": 5000,
                "reference": "new_approve_withdrawal",
                "narration": "911 Transaction",
                "destinationBankCode": bcode,
                "destinationAccountNumber": anumber,
                "currency": "NGN",
                "sourceAccountNumber": admin_wallet_number,
                "senderInfo": {
                    "sourceAccountNumber": "5232729933",
                    "sourceAccountName": "Eminent CodeTeck Enterprises",
                    # "sourceAccountBvn": "1234567890",
                    "senderBankCode": "50515"
                },

            }
        )

        print(response.content)
        data = json.loads(response.content)
        return data


def transfer():
    response = requests.post(
        "https://sandbox.monnify.com/api/v2/disbursements/single/validate-otp",
        headers,
        json={
            "reference": "refere--n00ce---1290034",
            "authorizationCode": "491763"
        }
    )
