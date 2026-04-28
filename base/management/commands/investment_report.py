from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from base.models import Investment, InvestmentPayout


class Command(BaseCommand):
    help = 'Generate daily/weekly investment report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            choices=['daily', 'weekly', 'monthly'],
            default='daily',
            help='Report period',
        )

    def handle(self, *args, **options):
        period = options['period']
        today = timezone.now()
        
        if period == 'daily':
            start_date = today - timedelta(days=1)
            title = 'Daily Investment Report'
        elif period == 'weekly':
            start_date = today - timedelta(days=7)
            title = 'Weekly Investment Report'
        else:
            start_date = today - timedelta(days=30)
            title = 'Monthly Investment Report'
        
        self.stdout.write(self.style.MIGRATE_HEADING(title))
        self.stdout.write(f'Period: {start_date.date()} to {today.date()}')
        
        # New investments
        new_investments = Investment.objects.filter(
            created_at__gte=start_date,
            created_at__lte=today
        )
        self.stdout.write(f'\nNew Investments: {new_investments.count()}')
        for inv in new_investments:
            self.stdout.write(f'  - {inv.reference_code}: ₦{inv.amount:,.2f} ({inv.user.email})')
        
        # Payouts processed
        payouts = InvestmentPayout.objects.filter(
            processed_date__gte=start_date,
            processed_date__lte=today,
            status='completed'
        )
        total_paid = sum(p.total_amount for p in payouts)
        self.stdout.write(f'\nPayouts Processed: {payouts.count()}')
        self.stdout.write(f'Total Paid: ₦{total_paid:,.2f}')
        
        # Active investments summary
        active = Investment.objects.filter(status='active').count()
        completed = Investment.objects.filter(
            status='completed',
            completed_at__gte=start_date
        ).count()
        pending = Investment.objects.filter(status='pending').count()
        
        self.stdout.write(f'\nCurrent Status:')
        self.stdout.write(f'  Active: {active}')
        self.stdout.write(f'  Completed (this period): {completed}')
        self.stdout.write(f'  Pending: {pending}')