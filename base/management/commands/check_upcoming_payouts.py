from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from base.models import InvestmentPayout


class Command(BaseCommand):
    help = 'Check upcoming payouts for the next 7 days'

    def handle(self, *args, **options):
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        upcoming = InvestmentPayout.objects.filter(
            status='scheduled',
            scheduled_date__date__gte=today,
            scheduled_date__date__lte=next_week
        ).select_related('investment', 'investment__user').order_by('scheduled_date')
        
        if not upcoming.exists():
            self.stdout.write(self.style.SUCCESS('No upcoming payouts in the next 7 days.'))
            return
        
        self.stdout.write(self.style.MIGRATE_HEADING(f'Upcoming Payouts ({upcoming.count()})'))
        
        current_date = None
        for payout in upcoming:
            payout_date = payout.scheduled_date.date()
            
            if payout_date != current_date:
                current_date = payout_date
                self.stdout.write(self.style.MIGRATE_HEADING(f'\n{payout_date.strftime("%A, %d %B %Y")}'))
            
            self.stdout.write(
                f'  {payout.investment.user.email:30} '
                f'₦{payout.total_amount:>12,.2f} '
                f'({payout.investment.plan.get_name_display()})'
            )