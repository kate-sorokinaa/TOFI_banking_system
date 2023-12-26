from celery import shared_task
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.models import Card, BudgetSystem


@shared_task
def check_credit_card_payments():
    # Эту функцию нужно будет вызывать из celery beat в начале каждого месяца
    current_month = timezone.now().month
    credit_cards = Card.objects.filter(card_type="C")

    for credit_card in credit_cards:
        # Проверка и погашение задолженности для каждой кредитной карты(временно)
        if credit_card.balance < 0 and credit_card.last_payment_month != current_month:
            credit_card.balance = 0
            credit_card.last_payment_month = current_month
            credit_card.save()


@shared_task
def process_pending_deposits():
    # Get cards with pending deposits
    cards = Card.objects.filter(is_deposit_allowed=True, pending_deposit_amount__gt=0)

    for card in cards:
        # Process the deposit and update the balance
        card.balance += card.pending_deposit_amount
        card.pending_deposit_amount = 0
        card.save()
        user_id = card.user.id

        # Log the deposit in the admin panel
        content_type = ContentType.objects.get_for_model(card)
        LogEntry.objects.create(
            user_id=user_id,  # Use the appropriate user ID
            content_type_id=content_type.id,
            object_id=card.id,
            object_repr=str(card),
            action_flag=CHANGE,
            change_message="Manual deposit processed.",
        )


@shared_task
def recount_daily_budget():
    cards = Card.objects.filter(using_system=True)

    for card in cards:
        system = BudgetSystem.objects.filter(card=card.id).first()
        if system.daily_redirect and (system.savings_card is not None):
            card.balance -= card.daily_balance
            card.daily_balance = 0
            system.savings_card.balance += card.daily_balance
            card.save()
            system.savings_card.save()
        if card.balance > card.fixated_sum:
            card.daily_balance += card.fixated_sum
        else:
            card.daily_balance += card.balance
        card.save()


@shared_task()
def count_monthly_budget_all():
    cards = Card.objects.filter(using_system=True)

    for card in cards:
        count_monthly_budget(card.id)


def count_monthly_budget(card_id):
    card = Card.objects.filter(id=card_id).first()
    system = BudgetSystem.objects.filter(card=card.id).first()
    if system.daily_control:
        card.fixated_sum = card.balance * system.daily_percent / 100
        card.daily_balance = card.fixated_sum
        card.save()
    if system.savings_card is not None:
        system.savings_card.balance += card.balance * system.savings_percent / 100
        system.savings_card.save()
