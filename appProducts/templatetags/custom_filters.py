from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def multiply(value, arg):
    """
    Умножает значение на аргумент.
    Использование: {{ price|multiply:quantity }}
    """
    try:
        if hasattr(value, 'amount'):  # MoneyField
            return Decimal(str(value.amount)) * Decimal(str(arg))
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, AttributeError):
        return 0


@register.filter
def currency(value):
    """
    Форматирует число как валюту.
    Использование: {{ price|currency }}
    """
    try:
        if hasattr(value, 'amount'):  # MoneyField
            return f"{value.amount:,.2f} ₽"
        return f"{float(value):,.2f} ₽"
    except (ValueError, TypeError):
        return "0,00 ₽"


@register.filter
def get_total_price(cart_items):
    """
    Вычисляет общую стоимость корзины.
    Использование: {{ cart_items|get_total_price }}
    """
    try:
        total = sum(
            item.product.price.amount * item.quantity 
            for item in cart_items
        )
        return f"{total:,.2f} ₽"
    except (AttributeError, TypeError):
        return "0,00 ₽"


@register.simple_tag
def cart_item_total(item):
    """
    Вычисляет стоимость одной позиции в корзине.
    Использование: {% cart_item_total item %}
    """
    try:
        return item.product.price.amount * item.quantity
    except (AttributeError, TypeError):
        return 0
