from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Payout


@transaction.atomic
def generate_payouts(investment):
    """
    Creates payout schedule based on plan
    """

    plan = investment.plan
    total_return = investment.total_expected_return
    payout_amount = total_return / plan.payout_count

    for i in range(1, plan.payout_count + 1):
        due_date = investment.start_date + timezone.timedelta(
            days=30 * plan.payout_interval_months * i
        )

        Payout.objects.create(
            investment=investment,
            amount=payout_amount,
            due_date=due_date
        )