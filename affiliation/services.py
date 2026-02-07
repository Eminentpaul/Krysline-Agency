from django.db import transaction
from decimal import Decimal
from .models import CommissionLog


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
