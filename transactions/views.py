from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView

from transactions.forms import FundTransferForm, FundTransferByCardForm
from accounts.models import Card, Payment, BudgetSystem


class TransactionMenu(TemplateView):
    template_name = "transactions/transaction_menu.html"


@login_required
def fund_transfer(request, card_id=None):
    card = get_object_or_404(Card, id=card_id) if card_id else 1

    if request.method == "POST":
        form = FundTransferForm(request.user, request.POST)
        if form.is_valid():
            receiver_account_number = form.cleaned_data["receiver_account_number"]
            amount = form.cleaned_data["amount"]
            selected_card = form.cleaned_data["card"]
            sender_card = Card.objects.get(id=selected_card.id)

            try:
                receiver_card = Card.objects.get(account_no=receiver_account_number)
            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect("transactions:fund_transfer")

            # Проверка баланса
            if selected_card.card_type != "C" and amount > sender_card.balance:
                messages.error(request, f"Insufficient funds to transfer.")
                return redirect("transactions:fund_transfer")

            if sender_card.using_system:
                system = BudgetSystem.objects.filter(card=sender_card).first()
                if system.daily_control and amount > sender_card.daily_balance:
                    messages.error(
                        request, "Insufficient funds out of your budget to transfer."
                    )
                    return redirect("transactions:fund_transfer")

            if sender_card == receiver_card:
                messages.error(
                    request, "Cannot transfer funds from and to the same card."
                )
                return redirect("transactions:fund_transfer")
            usd_in_rate = 3.19

            if usd_in_rate is None:
                usd_in_rate = 3.116  # default, if api not working
            if (
                sender_card.currency == "U"
                and sender_card.currency != receiver_card.currency
            ):
                # from belarusbank api
                converted_amount = Decimal(str(amount)) * Decimal(str(usd_in_rate))
            elif (
                sender_card.currency == "B"
                and sender_card.currency != receiver_card.currency
            ):
                # from belarusbank api
                converted_amount = Decimal(str(amount)) / Decimal(str(usd_in_rate))
            else:
                converted_amount = amount

            try:
                with transaction.atomic():
                    sender_card.balance -= amount
                    if sender_card.using_system:
                        system = BudgetSystem.objects.filter(card=sender_card).first()
                        if system.daily_control:
                            sender_card.daily_balance -= amount
                    sender_card.save()

                    receiver_card.balance += converted_amount
                    receiver_card.save()

                    Payment.objects.create(
                        card=receiver_card,
                        amount=receiver_card.balance,
                        currency=receiver_card.currency,
                        card_type=receiver_card.card_type,
                        deposit_pending=True,
                    )
                    Payment.objects.create(
                        card=sender_card,
                        amount=sender_card.balance,
                        currency=sender_card.currency,
                        card_type=sender_card.card_type,
                    )

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect("transactions:fund_transfer")

            return redirect("accounts:card_list")
    else:
        form = FundTransferForm(request.user)

    return render(
        request, "transactions/fund_transfer.html", {"form": form, "card": card}
    )


@login_required
def fund_transfer_card_by_card(request, card_id=None):
    card = get_object_or_404(Card, id=card_id) if card_id else 1

    if request.method == "POST":
        form = FundTransferByCardForm(request.user, request.POST)
        if form.is_valid():
            card_one = form.cleaned_data["card_one"]
            card_two = form.cleaned_data["card_two"]
            amount = form.cleaned_data["amount"]

            sender_card = Card.objects.get(id=card_one.id)
            receiver_card = Card.objects.get(id=card_two.id)
            usd_in_rate = 3.19

            if usd_in_rate is None:
                usd_in_rate = 3.116  # default, if api not working
            print(usd_in_rate)
            try:
                with transaction.atomic():
                    # Check balance
                    if card_one.card_type != "C" and amount > sender_card.balance:
                        messages.error(request, "Insufficient funds to transfer.")
                        return redirect("transactions:fund_transfer_card_by_card")

                    if sender_card.using_system:
                        system = BudgetSystem.objects.filter(card=sender_card).first()
                        if system.daily_control and amount > sender_card.daily_balance:
                            messages.error(
                                request,
                                "Insufficient funds out of your budget to transfer.",
                            )
                            return redirect("transactions:fund_transfer")

                    # Check if sender and receiver cards are the same
                    if sender_card == receiver_card:
                        messages.error(
                            request, "Cannot transfer funds from and to the same card."
                        )
                        return redirect("transactions:fund_transfer_card_by_card")

                    conversion_rate = Decimal(usd_in_rate)

                    if sender_card.currency != receiver_card.currency:
                        if sender_card.currency == "U":
                            converted_amount = amount * conversion_rate
                        elif sender_card.currency == "B":
                            converted_amount = amount / conversion_rate
                    else:
                        converted_amount = amount

                    # Deduct amount from sender's balance
                    sender_card.balance -= amount
                    if sender_card.using_system:
                        system = BudgetSystem.objects.filter(card=sender_card).first()
                        if system.daily_control:
                            sender_card.daily_balance -= amount
                    sender_card.save()

                    # Increase amount to receiver's balance
                    receiver_card.balance += converted_amount
                    receiver_card.save()

                    # Record the transaction
                    Payment.objects.create(
                        card=sender_card,
                        amount=-amount,
                        currency=sender_card.currency,
                        card_type=sender_card.card_type,
                    )
                    Payment.objects.create(
                        card=receiver_card,
                        amount=converted_amount,
                        currency=receiver_card.currency,
                        card_type=receiver_card.card_type,
                        deposit_pending=True,
                    )

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return redirect("transactions:fund_transfer_card_by_card")

            return redirect("accounts:card_list")

    else:
        form = FundTransferByCardForm(request.user)

    return render(
        request,
        "transactions/fund_transfer_card_by_card.html",
        {"form": form, "card": card},
    )
