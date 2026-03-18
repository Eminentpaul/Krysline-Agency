# import requests
# from monnify.monnify import Monnify
# from base64 import b64encode
# import os
# import json
# from datetime import datetime
# # from .bank_codes import bank_codes_name


# # Bank names and it's codes
# bank_codes_name = [
#     ('044-Access Bank', 'Access Bank'),
#     ('063-Access Bank (Diamond)', 'Access Bank (Diamond)'),
#     ('070-Fidelity Bank', 'Fidelity Bank'),
#     ('011-First Bank of Nigeria', 'First Bank'),
#     ('214-First City Monument Bank', 'FCMB'),
#     ('058-Guaranty Trust Bank', 'GTB'),
#     ('50515-Moniepoint MFB', 'Moniepoint MFB'),
#     ('999992-OPay Digital Services Limited (OPay)', 'OPay'),
#     ('232-Sterling Bank', 'Sterling Bank'),
#     ('033-United Bank For Africa', 'UBA'),
#     ('035-Wema Bank', 'Wema Bank'),
#     ('057-Zenith Bank', 'Zenith Bank'),
# ]


# # MONNIFY AUTHENTICATION
# api_key = os.environ.get("Mon_Api_key")
# secret_key = os.environ.get("Mon_Secret_key")
# contract_code = os.environ.get("Contract_Code")

# # admin_bank_name = str(os.environ.get('bankName'))
# admin_account_number = os.environ.get("accountNumber")
# admin_bank_code = os.environ.get("bankCode")
# admin_bank_name = os.environ.get("bankName")
# admin_wallet_number = os.environ.get("walletNumber")


# # BaseUrls
# base_url = "https://api.monnify.com"

# data = f"{api_key}:{secret_key}".encode()
# apKey_Secret = b64encode(data).decode("ascii")


# def access_token(apKeySecretKey):
#     response = requests.post(
#         f"{base_url}/api/v1/auth/login",
#         headers={
#             "Authorization": f"Basic {apKeySecretKey}"
#         }
#     )

#     data = json.loads(response.content)

#     accessToken = str(data['responseBody']['accessToken'])

#     return accessToken


# accessTonken = access_token(apKey_Secret)

# headers = {
#     "Authorization": f"Bearer {accessTonken}",
#     "Content-Type": "application/json"
# }


# def get_bank_code(bank_name: str, codelist=bank_codes_name):

#     bank_map = {}

#     for bank in codelist:
#         try:
#             code, name = bank[0].split('-', 1)
#             bank_map[name.strip()] = code.strip()
#         except ValueError:
#             continue

#     try:
#         _, selected_name = bank_name.split('-', 1)
#     except ValueError:
#         raise ValueError("Invalid bank format")

#     return bank_map.get(selected_name.strip())


# def bank_verification(accountNumber, bankName):
#     accountNumber = str(accountNumber)
#     bankCode = get_bank_code(bank_name=bankName)

#     response = requests.get(
#         f"{base_url}/api/v1/disbursements/account/validate",
#         headers=headers,

#         params={
#             "accountNumber": accountNumber,
#             "bankCode": bankCode
#         }
#     )

#     data = json.loads(response.content)

#     if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
#         return data['responseBody'], True
#     else:
#         return data['responseMessage'], False


# def maskAccountNumber(number):
#     pre = str(number)[:3]
#     post = str(number)[-3:]

#     return str(f"{pre}****{post}")


# def create_invoice(amount, user, description, reference, expirydate):

#     response = requests.post(
#         f"{base_url}/api/v1/invoice/create",
#         headers=headers,
#         json={
#             "amount": amount,
#             "currencyCode": "NGN",
#             "invoiceReference": reference,
#             "customerName": user.get_full_name(),
#             "customerEmail": user.email,
#             "contractCode": contract_code,
#             "description": description,
#             "expiryDate": expirydate,

#             "redirectUrl": "https://royal-dilemmatical-tartishly.ngrok-free.dev/Dashboard/payments/",
#             "accountReference": ""
#         }
#     )
#     data = json.loads(response.content)
#     print(data)
#     if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
#         return data['responseBody'], True
#     else:
#         return data['responseMessage'], False


# def get_invoice(reference):
#     response = requests.get(
#         f"{base_url}/api/v1/invoice/{reference}/details",
#         headers={
#             "Authorization": f"Bearer {accessTonken}"
#         }
#     )

#     data = json.loads(response.content)

#     print("Get Invoice: ", data)

#     if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
#         return data['responseBody'], True
#     else:
#         return data['responseMessage'], False


# def cancle_invoice(reference):
#     response = requests.delete(
#         f"{base_url}/api/v1/invoice/{reference}/cancel",
#         headers={
#             "Authorization": f"Bearer {accessTonken}"
#         }
#     )

#     data = json.loads(response.content)
#     print("Cancle: ", data)

#     if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
#         return data['responseBody'], True
#     else:
#         return data['responseMessage'], False


# # def get_transaction(reference):
# #     response = requests.get(
# #             f"{base_url}/api/v2/transactions/{reference}",
# #             headers={
# #             "Authorization": f"Bearer {accessTonken}"
# #             }
# #         )

# #     data = json.loads(response.content)

# #     if data["requestSuccessful"] == True and data["responseMessage"] == 'success':
# #         return data['responseBody'], True
# #     else:
# #         return data['responseMessage'], False


# def initiate_transfer(accountNumber, bankName):

#     # {'accountNumber': '0570385531', 'accountName': 'OSHI PAULINUS OFFORBUIKE', 'bankCode': '058', 'currencyCode': 'NGN'}

#     # Setting the banks accounts
#     # admin_bank = bank_verification(admin_account_number, admin_bank_name)
#     destinationDetails, dvalid = bank_verification(
#         accountNumber=accountNumber, bankName=bankName)


#     if dvalid:
#         bcode = str(destinationDetails['bankCode'])
#         anumber = str(destinationDetails['accountNumber'])
#         cname = str(destinationDetails['accountName'])

#         response = requests.post(
#             f"{base_url}/api/v2/disbursements/single",
#             headers=headers,
#             json={
#                 "amount": 5000,
#                 "reference": "new_approve_withdrawal",
#                 "narration": "911 Transaction",
#                 "destinationBankCode": bcode,
#                 "destinationAccountNumber": anumber,
#                 "currency": "NGN",
#                 "sourceAccountNumber": admin_wallet_number,
#                 "senderInfo": {
#                     "sourceAccountNumber": "5232729933",
#                     "sourceAccountName": "Eminent CodeTeck Enterprises",
#                     # "sourceAccountBvn": "1234567890",
#                     "senderBankCode": "50515"
#                 },

#             }
#         )

#         print(response.content)
#         data = json.loads(response.content)
#         return data


# def transfer():
#     response = requests.post(
#         "https://sandbox.monnify.com/api/v2/disbursements/single/validate-otp",
#         headers,
#         json={
#             "reference": "refere--n00ce---1290034",
#             "authorizationCode": "491763"
#         }
#     )


import requests
from base64 import b64encode
import os
import json
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from functools import wraps

# Bank names and codes
BANK_CODES_NAME = [
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


class MonnifyAPIError(Exception):
    """Custom exception for Monnify API errors"""
    pass


class MonnifyClient:
    """Monnify API client with automatic token refresh"""

    def __init__(self):
        self.api_key = os.environ.get("Mon_Api_key")
        self.secret_key = os.environ.get("Mon_Secret_key")
        self.contract_code = os.environ.get("Contract_Code")
        self.base_url = "https://api.monnify.com"

        # Admin credentials
        self.admin_account_number = os.environ.get("accountNumber")
        self.admin_bank_code = os.environ.get("bankCode")
        self.admin_bank_name = os.environ.get("bankName")
        self.admin_wallet_number = os.environ.get("walletNumber")

        self._access_token = None
        self._token_expiry = None

        # Validate credentials
        if not all([self.api_key, self.secret_key, self.contract_code]):
            raise ValueError(
                "Missing required Monnify credentials in environment")

    def _get_auth_string(self) -> str:
        """Generate Base64 encoded API key and secret"""
        data = f"{self.api_key}:{self.secret_key}".encode()
        return b64encode(data).decode("ascii")

    def _refresh_token(self) -> str:
        """Fetch new access token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                headers={"Authorization": f"Basic {self._get_auth_string()}"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("requestSuccessful") and data.get("responseMessage") == "success":
                self._access_token = data["responseBody"]["accessToken"]
                # Token typically expires in 1 hour, refresh after 50 minutes
                self._token_expiry = datetime.now().timestamp() + 3000
                return self._access_token
            else:
                raise MonnifyAPIError(
                    f"Token refresh failed: {data.get('responseMessage')}")

        except requests.exceptions.RequestException as e:
            raise MonnifyAPIError(f"Failed to authenticate: {str(e)}")

    @property
    def access_token(self) -> str:
        """Get valid access token, refresh if expired"""
        if not self._access_token or datetime.now().timestamp() >= (self._token_expiry or 0):
            return self._refresh_token()
        return self._access_token

    @property
    def headers(self) -> Dict[str, str]:
        """Get authorization headers with current token"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[Any, bool]:
        """Generic request handler with error handling"""
        url = f"{self.base_url}{endpoint}"
        timeout = kwargs.pop('timeout', 30)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()

            # Try to parse JSON, handle empty responses
            try:
                data = response.json()
            except json.JSONDecodeError:
                if response.status_code == 204:
                    return None, True
                return f"Invalid JSON response: {response.text}", False

            # Check Monnify-specific success indicators
            if data.get("requestSuccessful") is True and data.get("responseMessage") == "success":
                return data.get("responseBody"), True
            else:
                error_msg = data.get("responseMessage", "Unknown API error")
                print(f"Monnify API Error: {error_msg}")
                return error_msg, False

        except requests.exceptions.Timeout:
            return "Request timeout", False
        except requests.exceptions.ConnectionError:
            return "Connection error", False
        except requests.exceptions.HTTPError as e:
            return f"HTTP {response.status_code}: {str(e)}", False
        except requests.exceptions.RequestException as e:
            return f"Request failed: {str(e)}", False
        except Exception as e:
            return f"Unexpected error: {str(e)}", False


# Global client instance
monnify = MonnifyClient()


def get_bank_code(bank_name: str) -> Optional[str]:
    """Extract bank code from formatted bank name"""
    bank_map = {}

    for bank in BANK_CODES_NAME:
        try:
            code, name = bank[0].split('-', 1)
            bank_map[name.strip()] = code.strip()
        except ValueError:
            continue

    try:
        _, selected_name = bank_name.split('-', 1)
    except ValueError:
        raise ValueError(f"Invalid bank format: {bank_name}")

    return bank_map.get(selected_name.strip())


def verify_bank_account(account_number: str, bank_name: str) -> Tuple[Any, bool]:
    """Verify bank account details"""
    try:
        bank_code = get_bank_code(bank_name)
        if not bank_code:
            return "Invalid bank name", False

        response, success = monnify._make_request(
            "GET",
            "/api/v1/disbursements/account/validate",
            params={
                "accountNumber": str(account_number),
                "bankCode": bank_code
            }
        )
        return response, success

    except Exception as e:
        return str(e), False


def mask_account_number(number: str) -> str:
    """Mask account number showing first 3 and last 3 digits"""
    num_str = str(number)
    if len(num_str) < 6:
        return num_str
    return f"{num_str[:3]}****{num_str[-3:]}"


def create_invoice(
    amount: float,
    user,
    description: str,
    reference: str,
    expiry_date: str,
    redirect_url: Optional[str] = None
) -> Tuple[Any, bool]:
    """Create payment invoice"""

    payload = {
        "amount": amount,
        "currencyCode": "NGN",
        "invoiceReference": reference,
        "customerName": user.get_full_name() or user.username,
        "customerEmail": user.email,
        "contractCode": monnify.contract_code,
        "description": description,
        "expiryDate": expiry_date,
        "redirectUrl": redirect_url or "https://royal-dilemmatical-tartishly.ngrok-free.dev/Dashboard/payments/", #"https://affiliate.kagency.org/Dashboard/payments/",
        "accountReference": ""
    }

    return monnify._make_request("POST", "/api/v1/invoice/create", json=payload)


def get_invoice_details(reference: str) -> Tuple[Any, bool]:
    """Get invoice details by reference"""
    return monnify._make_request(
        "GET",
        f"/api/v1/invoice/{reference}/details"
    )


def cancel_invoice(reference: str) -> Tuple[Any, bool]:
    """Cancel an existing invoice"""
    return monnify._make_request(
        "DELETE",
        f"/api/v1/invoice/{reference}/cancel"
    )


def initiate_transfer(
    amount: float,
    reference: str,
    narration: str,
    destination_account: str,
    destination_bank_name: str,
    source_account: Optional[str] = None
) -> Tuple[Any, bool]:
    """Initiate single disbursement transfer"""

    # Verify destination account
    dest_details, valid = verify_bank_account(
        destination_account, destination_bank_name)
    if not valid:
        return "Invalid destination account", False

    payload = {
        "amount": amount,
        "reference": reference,
        "narration": narration,
        "destinationBankCode": dest_details["bankCode"],
        "destinationAccountNumber": dest_details["accountNumber"],
        "currency": "NGN",
        "sourceAccountNumber": source_account or monnify.admin_wallet_number,
    }

    return monnify._make_request(
        "POST",
        "/api/v2/disbursements/single",
        json=payload
    )


def validate_transfer_otp(reference: str, otp: str) -> Tuple[Any, bool]:
    """Validate OTP for transfer"""
    payload = {
        "reference": reference,
        "authorizationCode": otp
    }

    return monnify._make_request(
        "POST",
        "/api/v2/disbursements/single/validate-otp",
        json=payload
    )


# Backward compatibility aliases
def access_token(): return monnify.access_token


bank_verification = verify_bank_account
maskAccountNumber = mask_account_number
cancle_invoice = cancel_invoice  # Fix typo
get_invoice = get_invoice_details
