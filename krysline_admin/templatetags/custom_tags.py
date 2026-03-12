from django import template
from affiliation.models import AffiliatePackage
from ledger.models import FinancialEntry
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
    partition = math.ceil(len(value[:at])/3) - 1
    pre = value[:at][:partition]
    post = value[:at][-partition:]
    domain = value[at:]
    middle = "*" * (partition+1)

    return f"{pre}{middle}{post}{domain}"



# @register.filter(name="entry_type_label")
# def entry_type_label(value):

#     if not value or not hasattr(value, "reference_id"):
#         return "Unknown"

#     ref = value.reference_id.upper()

#     if ref.startswith("EXP"):
#         return "Expenses"

#     elif ref.startswith("PKG"):
#         return "Package Subscription"

#     elif ref.startswith("WTH"):
#         return "Withdrawal"

#     elif ref.startswith("PROP"):
#         return "Property Sale"

#     return "Other"
    
    

@register.filter(name="entry_category_label")
def entry_category_label(value):
    return dict(value.CATEGORIES).get(value.category, "Other")

