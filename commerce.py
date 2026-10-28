"""Validated stock and money helpers shared by marketplace and checkout.

Stock uses the unit entered by the farmer. Orders currently buy whole units;
we never infer a count from an ambiguous legacy description such as '5 x 10 kg'.
"""
import re
from decimal import Decimal, InvalidOperation

_STOCK = re.compile(
    r'^(\d+(?:\.\d{1,3})?)\s*(kg|g|l|ml|litres?|liters?|pieces?|units?|dozen|bunch(?:es)?|bags?|quintals?|tonnes?)?$',
    re.IGNORECASE,
)
MAX_QUANTITY = 500
MAX_TOTAL_PAISE = 1_000_000_000


def parse_stock(value):
    text = str(value or '').strip()
    match = _STOCK.fullmatch(text) if len(text) <= 50 else None
    if not match:
        raise ValueError('Enter available stock as a number and unit, for example 100 kg or 20 pieces.')
    amount = Decimal(match.group(1))
    if amount > Decimal('1000000000'):
        raise ValueError('Available stock is too large.')
    return amount, (match.group(2) or 'unit').lower()


def stock_text(amount, unit):
    number = format(amount, 'f').rstrip('0').rstrip('.') if '.' in format(amount, 'f') else format(amount, 'f')
    return f'{number or "0"} {unit}'


def price_paise(value):
    try:
        if len(str(value)) > 32:
            raise ValueError
        amount = Decimal(str(value))
        if not amount.is_finite() or not Decimal('0.01') <= amount <= Decimal('1000000'):
            raise ValueError
        paise = amount * 100
        if paise != paise.to_integral_value():
            raise ValueError
        return int(paise)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Price must be between ₹0.01 and ₹10,00,000 with at most two decimal places.') from None


def order_quantity(value, allow_zero=False):
    raw = str(value or '')
    if not re.fullmatch(r'\d{1,3}', raw):
        raise ValueError('Choose a whole-number quantity between 1 and 500.')
    quantity = int(raw)
    if not (0 if allow_zero else 1) <= quantity <= MAX_QUANTITY:
        raise ValueError('Choose a whole-number quantity between 1 and 500.')
    return quantity
