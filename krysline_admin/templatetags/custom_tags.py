from django import template
from affiliation.models import AffiliatePackage
from decimal import Decimal
import math
packages = AffiliatePackage.objects.all()

register = template.Library()

@register.filter
def package_name(value):
    return f"{value.name}".capitalize()


@register.filter
def package_price(value):
    return value.price



@register.filter
def package_income(value):
    total = 0
    package = value.members.all()
    for amount in package:
        total += int(amount.package.price)

    total = Decimal(str(total))
    return (total)



@register.filter
def mask_email(value):
    at = value.index("@")
    partition = math.ceil(len(value[:at])/3) -1
    pre = value[:at][:partition]
    post = value[:at][-partition:]
    domain = value[at:]
    middle = "*" * (partition+1)

    return f"{pre}{middle}{post}{domain}"


# mask_email('oshipaulinus@gmail.com')