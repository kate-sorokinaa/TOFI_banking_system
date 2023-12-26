from decimal import Decimal, getcontext


def convert_currency(amount, from_currency, to_currency, rate):
    valid_currencies = {"USD", "BYN", "U", "B"}

    if from_currency not in valid_currencies or to_currency not in valid_currencies:
        raise ValueError("Invalid currency code")

    if from_currency == to_currency:
        return amount
    else:
        # Устанавливаем точность для объектов Decimal
        getcontext().prec = 10

        amount = Decimal(str(amount))
        rate = Decimal(str(rate))
        result = amount / rate

        return result
