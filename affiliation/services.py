from django.db import transaction
from decimal import Decimal
from .models import CommissionLog, AffiliatePackage, Affiliate
from authentication.models import User
from django.shortcuts import get_object_or_404
import requests
from dotenv import load_dotenv
import os

load_dotenv()


@transaction.atomic
def distribute_commissions(new_user_profile):
    """
    Traverse the upline and distribute registration percentages based on package depth.
    """
    package = new_user_profile.package
    current_upline = new_user_profile.referrer
    gen = 1

    while current_upline and gen <= 3:
        # Check if upline's package supports this depth
        if gen <= current_upline.package.generations:
            # Use 'match' for clean percentage selection
            match gen:
                case 1: pct = current_upline.package.commissions.get('1', 0)
                case 2: pct = current_upline.package.commissions.get('2', 0)
                case 3: pct = current_upline.package.commissions.get('3', 0)
                case _: pct = 0

            if pct > 0:
                reward = (new_user_profile.package.price * Decimal(pct)) / 100
                current_upline.balance += reward
                current_upline.save()

                CommissionLog.objects.create(
                    recipient=current_upline,
                    amount=reward,
                    source_user=new_user_profile.user,
                    generation=gen
                )
        
        current_upline = current_upline.referrer
        gen += 1



def verify_transaction_with_api(transaction_id, user):
    import paystack

    paystack.api_key(os.environ.get('SECRET_KEY'))

    paystack.Transaction.fetch
    """
    Step 2: Server-to-Server re-verification
    """
    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    headers = {
        "Authorization": f"Bearer {os.environ.get('SECRET_KEY')}",
        "Content-Type": "application/json"
    }


    

    try:
        response = requests.get(url, headers=headers)
        res_data = response.json()

        if res_data["status"] == "success" and res_data["data"]["status"] == "successful":
            data = res_data["data"]
            # Fetch the pending affiliate record using the reference
            # tx_ref was generated in the 'process_payment' view
            
            with transaction.atomic():
                package = get_object_or_404(AffiliatePackage, price=float(data['amount']))
                try:
                    affiliate = Affiliate.objects.select_for_update().get(referral_code=str(user.affiliate_record.referral_code))
                    
                    if float(data["amount"]) >= package.price and data["currency"] == "NGN":
                        # SUCCESS: Activate user and trigger MLM Commissions
                        affiliate.is_active = True
                        affiliate.save()
                        
                        # Trigger your MLM commission distribution logic
                        # distribute_commissions(affiliate.user.profile)

                        # print("Normal Ziko")
                        return True
                    

                except Affiliate.DoesNotExist:
                    Affiliate.objects.create(
                        user = user,
                        package = package
                    )

                
                # Critical check: Does the paid amount match the package price?
                
                    
    except Exception as e:
        print(f"Verification Error: {e}")
        
    
    return False
