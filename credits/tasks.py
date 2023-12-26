from datetime import datetime

from celery import shared_task

from accounts.models import Card
from .models import Credit


@shared_task
def process_monthly_payment():
    # Получить все активные кредиты, для которых не был проведен ежемесячный платеж
    credits = Credit.objects.filter(
        status="APPROVED", updated_at__month=datetime.now().month
    )

    for credit in credits:
        # Получить карту, привязанную к кредиту
        card = Card.objects.get(user=credit.user, card_name=f"{credit.purpose} Credit")

        # Вычесть ежемесячный платеж из баланса карты
        card.balance -= credit.monthly_payment
        card.save()

        # Обновить оставшуюся сумму по кредиту
        credit.remaining_amount -= credit.monthly_payment

        # Уменьшить количество оставшихся месяцев
        credit.term_months -= 1
        credit.save()

        # Если кредит выплачен, обновить статус
        if credit.remaining_amount <= 0:
            credit.status = "PAID"
            credit.term_months = (
                0  # Убедитесь, что месяцы равны нулю, если кредит выплачен
            )
            credit.save()
