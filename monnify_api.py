import requests
from monnify.monnify import Monnify
from base64 import b64encode
import base64
import os
from datetime import datetime
from monnify_verification.monnify_api import *



data = initiate_transfer(accountNumber="8143122946", bankName="999992-OPay Digital Services Limited (OPay)")

print(data)



