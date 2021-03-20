from decimal import Decimal, ROUND_DOWN, ROUND_UP, ROUND_HALF_UP

def round(number, rounding):
    if not rounding:
        return number

    return number.quantize(Decimal('0.00'), rounding=rounding).normalize()


# Dokladne obliczenia
#TAX_TRANSACTION_COST_ROUNDING = None
#TAX_TRANSACTION_GAIN_ROUNDING = None
#TAX_ACCOUNT_COST_ROUNDING = ROUND_HALF_UP
#TAX_ACCOUNT_GAIN_ROUNDING = ROUND_HALF_UP

#TAX_TRANSACTION_DIVIDEND_TAX_BASE_ROUNDING = None
#TAX_TRANSACTION_DIVIDEND_TAX_PAYED_ROUNDING = None
#TAX_ACCOUNT_DIVIDEND_TAX_BASE_ROUNDING = ROUND_HALF_UP
#TAX_ACCOUNT_DIVIDEND_TAX_PAYED_ROUNDING = ROUND_HALF_UP

# Maksymalizacja podatku - bezpieczne
TAX_TRANSACTION_COST_ROUNDING = ROUND_DOWN
TAX_TRANSACTION_GAIN_ROUNDING = ROUND_UP
TAX_ACCOUNT_COST_ROUNDING = None
TAX_ACCOUNT_GAIN_ROUNDING = None

TAX_TRANSACTION_DIVIDEND_TAX_BASE_ROUNDING = ROUND_UP
TAX_TRANSACTION_DIVIDEND_TAX_PAYED_ROUNDING = ROUND_DOWN
TAX_ACCOUNT_DIVIDEND_TAX_BASE_ROUNDING = None
TAX_ACCOUNT_DIVIDEND_TAX_PAYED_ROUNDING = None

# Zaokraglenia tranzakcji
#TAX_TRANSACTION_COST_ROUNDING = ROUND_HALF_UP
#TAX_TRANSACTION_GAIN_ROUNDING = ROUND_HALF_UP
#TAX_ACCOUNT_COST_ROUNDING = None
#TAX_ACCOUNT_GAIN_ROUNDING = None

#TAX_TRANSACTION_DIVIDEND_TAX_BASE_ROUNDING = ROUND_HALF_UP
#TAX_TRANSACTION_DIVIDEND_TAX_PAYED_ROUNDING = ROUND_HALF_UP
#TAX_ACCOUNT_DIVIDEND_TAX_BASE_ROUNDING = None
#TAX_ACCOUNT_DIVIDEND_TAX_PAYED_ROUNDING = None