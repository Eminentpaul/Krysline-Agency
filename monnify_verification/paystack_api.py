import paystack
import os
from dotenv import load_dotenv


load_dotenv()


Secret_key = os.environ.get("PAYSTACK_SECRET_KEY")

paystack.api_key = Secret_key

