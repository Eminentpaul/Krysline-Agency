from django import template

register = template.Library()

@register.filter
def calculate_return(plan, amount):
    """Calculate return for a plan given an investment amount"""
    return plan.calculate_total_return(amount)