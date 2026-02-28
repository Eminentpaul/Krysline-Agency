from django.utils import timezone
from affiliation.models import Affiliate
import structlog

logger = structlog.get_logger(__name__)

def check_expired_subscriptions():
    """
    Finds all active affiliates whose duration has passed 
    and deactivates them in bulk.
    """
    today = timezone.now()
    
    # 1. Use filter().update() for high speed
    # This hits the database ONCE, even if 1,000 people expired
    expired_count = Affiliate.objects.filter(
        is_active=True,
        duration__lt=today # __lt means "Less Than" (Past Date)
    ).update(is_active=False)

    if expired_count > 0:
        logger.info(f"System: Deactivated {expired_count} expired KAL accounts.")
        return True
    else: return False
