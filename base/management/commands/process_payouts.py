#!/usr/bin/env python
"""
Management command to process scheduled investment payouts.
Run via: python manage.py process_payouts
Or via cron: 0 9 * * * /usr/bin/python3 /path/to/manage.py process_payouts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.core.mail import EmailMessage, get_connection
from decimal import Decimal
from dotenv import load_dotenv
from django.conf import settings
import os
from base.models import Investment, InvestmentPayout, InvestmentStatus

load_dotenv()

email = settings.EMAIL_HOST_USER


class Command(BaseCommand):
    help = 'Process scheduled investment payouts and update investment statuses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Process payouts for specific date (YYYY-MM-DD)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Determine date to process
        if options['date']:
            from datetime import datetime
            process_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            process_date = timezone.now().date()
        
        self.stdout.write(self.style.MIGRATE_HEADING(f'Processing payouts for {process_date}'))
        
        # Find payouts scheduled for today
        due_payouts = InvestmentPayout.objects.filter(
            status='scheduled',
            scheduled_date__date=process_date,
            investment__status='active'
        ).select_related('investment', 'investment__user', 'investment__plan')
        
        if not due_payouts.exists():
            self.stdout.write(self.style.WARNING('No payouts due for processing.'))
            return
        
        self.stdout.write(f'Found {due_payouts.count()} payouts to process')
        
        processed = 0
        failed = 0
        
        for payout in due_payouts:
            try:
                with transaction.atomic():
                    result = self.process_payout(payout, dry_run)
                    if result:
                        processed += 1
                    else:
                        failed += 1
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f'Failed to process payout {payout.id}: {str(e)}')
                )
        
        # Update investment statuses
        completed = self.update_investment_statuses(dry_run)
        
        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING('Processing Summary'))
        self.stdout.write(f'Date: {process_date}')
        self.stdout.write(f'Payouts processed: {processed}')
        self.stdout.write(f'Payouts failed: {failed}')
        self.stdout.write(f'Investments completed: {completed}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made'))

    def process_payout(self, payout, dry_run=False):
        """Process a single payout"""
        investment = payout.investment
        user = investment.user
        
        self.stdout.write(f'Processing payout #{payout.payout_number} for {investment.reference_code}')
        self.stdout.write(f'  User: {user.email}')
        self.stdout.write(f'  Amount: ₦{payout.total_amount:,.2f}')
        
        if dry_run:
            return True
        
        # Update payout
        payout.status = 'completed'
        payout.processed_date = timezone.now()
        payout.payment_reference = f'AUTO-{timezone.now().strftime("%Y%m%d%H%M%S")}-{payout.id}'
        payout.save()
        
        # Update investment totals
        investment.total_paid_out += payout.total_amount
        investment.payouts_completed += 1
        investment.save(update_fields=['total_paid_out', 'payouts_completed'])

        # Update user account balance for withdrawing 
        user.profile.balance += payout.total_amount
        user.profile.save()
        
        # Create transaction record
        # from financial.models import Transaction  # Adjust import as needed
        # Transaction.objects.create(
        #     user=user,
        #     amount=payout.total_amount,
        #     transaction_type='investment_payout',
        #     description=f'Payout #{payout.payout_number} for {investment.plan.get_name_display()}',
        #     status='completed',
        #     reference=payout.payment_reference
        # )
        
        # Send notification
        self.send_payout_notification(payout)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Payout processed successfully'))
        return True

    def update_investment_statuses(self, dry_run=False):
        """Mark investments as completed when all payouts are done"""
        # Find active investments with all payouts completed
        investments_to_complete = Investment.objects.filter(
            status='active'
        ).exclude(
            payouts__status__in=['scheduled', 'processing']
        ).filter(
            payouts__status='completed'
        ).distinct()
        
        completed_count = 0
        
        for investment in investments_to_complete:
            total_payouts = investment.payouts.count()
            completed_payouts = investment.payouts.filter(status='completed').count()
            
            if total_payouts == completed_payouts and total_payouts > 0:
                self.stdout.write(
                    f'Completing investment {investment.reference_code} '
                    f'({completed_payouts}/{total_payouts} payouts)'
                )
                
                if not dry_run:
                    investment.status = InvestmentStatus.COMPLETED
                    investment.completed_at = timezone.now()
                    investment.save(update_fields=['status', 'completed_at'])
                    
                    # Send completion notification
                    self.send_completion_notification(investment)
                
                completed_count += 1
        
        return completed_count

    def send_payout_notification(self, payout):
        """Send email notification to user"""
        with  get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            # use_ssl=settings.EMAIL_USE_SSL
            use_tls=settings.EMAIL_USE_TLS
        ) as connection:
            try:
                user = payout.investment.user
                plan_name = payout.investment.plan.get_name_display()
                
                subject = f'Investment Payout Received - {plan_name}'
                message = f'''
    Dear {user.get_full_name() or user.username},

    Your investment payout has been processed successfully.

    Investment: {plan_name}
    Payout Number: #{payout.payout_number} of {payout.investment.plan.total_payouts}
    Amount Received: ₦{payout.total_amount:,.2f}
    Principal: ₦{payout.principal_amount:,.2f}
    Returns: ₦{payout.return_amount:,.2f}
    Date: {payout.processed_date.strftime("%d %B, %Y")}

    Reference: {payout.payment_reference}

    Thank you for investing with Krysline Agency.

    Best regards,
    Krysline Agency Team
                '''
                
                # send_mail(
                #     subject=subject,
                #     message=message,
                #     from_email=email,
                #     recipient_list=[f"{user.email}", ],
                #     fail_silently=True,
                # )
                EmailMessage(subject, message, email, [f"{user.email}", ], connection=connection).send(fail_silently=True,)
                print("Payout Notificate sent")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to send notification: {str(e)}')
                )

    def send_completion_notification(self, investment):
        """Send investment completion notification"""
        try:
            user = investment.user
            plan_name = investment.plan.get_name_display()
            
            subject = f'Investment Completed - {plan_name}'
            message = f'''
Dear {user.get_full_name() or user.username},

Congratulations! Your investment has been fully completed.

Investment: {plan_name}
Total Invested: ₦{investment.amount:,.2f}
Total Returns: ₦{investment.total_paid_out:,.2f}
Duration: {investment.plan.duration_display}
Completed: {investment.completed_at.strftime("%d %B, %Y")}

Thank you for trusting Krysline Agency with your investment.

Best regards,
Krysline Agency Team
            '''
            
            send_mail(
                subject=subject,
                message=message,
                from_email=email,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Failed to send completion notification: {str(e)}')
            )