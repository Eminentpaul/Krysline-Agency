from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, User
from affiliation.models import UserInvoice



@receiver(post_save, sender=User)
def create_user_security_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)



@receiver(post_save, sender=User)
def create_user_inoice(sender, instance, created, **kwargs):
    if created:
        UserInvoice.objects.create(user=instance)