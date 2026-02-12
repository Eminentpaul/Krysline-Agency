from django.db import transaction
from decimal import Decimal
from .models import CommissionLog, AffiliatePackage, Affiliate
from authentication.models import User
from django.shortcuts import get_object_or_404
import requests
from dotenv import load_dotenv
import os
from security.decorators import *

load_dotenv()


# @transaction.atomic
# def distribute_commissions(new_user_profile):
#     """
#     Traverse the upline and distribute registration percentages based on package depth.
#     """
#     package = new_user_profile.package
#     print(package)
#     current_upline = new_user_profile.referrer
#     gen = 1

#     while current_upline and gen <= 3:
#         # Check if upline's package supports this depth
#         if gen <= current_upline.package.generations:
#             # Use 'match' for clean percentage selection
#             match gen:
#                 case 1: pct = current_upline.package.commissions.get('1', 0)
#                 case 2: pct = current_upline.package.commissions.get('2', 0)
#                 case 3: pct = current_upline.package.commissions.get('3', 0)
#                 case _: pct = 0

#             if pct > 0:
#                 reward = (new_user_profile.package.price * Decimal(pct)) / 100
#                 current_upline.balance += reward
#                 current_upline.save()

#                 CommissionLog.objects.create(
#                     recipient=current_upline,
#                     amount=reward,
#                     source_user=new_user_profile.user,
#                     generation=gen
#                 )
        
#         current_upline = current_upline.referrer
#         gen += 1



@transaction.atomic
def distribute_commissions(new_affiliate):
    """
    Climbs the MLM tree and pays uplines based on their package depth.
    """
    # The person who just paid
    payment_amount = new_affiliate.package.price
    # The first person to get paid (The Referrer)
    current_upline_profile = new_affiliate.user.profile.referrer
    
    gen = 1
    # KAL Policy: We only pay up to 3 generations
    while current_upline_profile and gen <= 3:
        # Get the upline's business record to check their package
        upline_affiliate = getattr(current_upline_profile.user, 'affiliate_record', None)
        
        if upline_affiliate and upline_affiliate.is_active:
            upline_package = upline_affiliate.package
            
            # Check if their package allows earning at this depth (Gen 1, 2, or 3)
            if gen <= upline_package.generations:
                # Pull percentage from the JSONField we created: {"1": 20, "2": 10...}
                percentage = upline_package.commissions.get(str(gen), 0)
                
                if percentage > 0:
                    commission_amount = (payment_amount * Decimal(percentage)) / Decimal(100)
                    
                    # 1. Update Balance (Securely)
                    current_upline_profile.balance += commission_amount
                    current_upline_profile.save()
                    
                    # 2. Create Audit Log
                    CommissionLog.objects.create(
                        recipient_profile=current_upline_profile,
                        amount=commission_amount,
                        source_user=new_affiliate.user,
                        generation=gen
                    )
                    
                    logger.info(f"Commission Paid: {commission_amount} to {current_upline_profile.user.email}")

        # Move up to the next boss in the tree
        current_upline_profile = current_upline_profile.referrer
        gen += 1

        # print('Commission')

        # return True



# ==================================================
# Flutterwave transaction verification 
# ==================================================


# def verify_transaction_with_api(transaction_id, user):
#     import paystack
#     """
#     Step 2: Server-to-Server re-verification
#     """
#     url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
#     headers = {
#         "Authorization": f"Bearer {os.environ.get('SECRET_KEY')}",
#         "Content-Type": "application/json"
#     }


    

#     try:
#         response = requests.get(url, headers=headers)
#         res_data = response.json()

#         if res_data["status"] == "success" and res_data["data"]["status"] == "successful":
#             data = res_data["data"]
#             # Fetch the pending affiliate record using the reference
#             # tx_ref was generated in the 'process_payment' view
            
#             with transaction.atomic():
#                 package = get_object_or_404(AffiliatePackage, price=float(data['amount']))
#                 try:
#                     affiliate = Affiliate.objects.select_for_update().get(referral_code=str(user.affiliate_record.referral_code))
                    
#                     if float(data["amount"]) >= package.price and data["currency"] == "NGN":
#                         # SUCCESS: Activate user and trigger MLM Commissions
#                         affiliate.is_active = True
#                         affiliate.save()
                        
#                         # Trigger your MLM commission distribution logic
#                         # distribute_commissions(affiliate.user.profile)

#                         # print("Normal Ziko")
#                         return True
                    

#                 except Affiliate.DoesNotExist:
#                     Affiliate.objects.create(
#                         user = user,
#                         package = package
#                     )

                
#                 # Critical check: Does the paid amount match the package price?
                
                    
#     except Exception as e:
#         print(f"Verification Error: {e}")
        
    
#     return False
