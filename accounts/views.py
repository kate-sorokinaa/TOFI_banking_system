from datetime import timedelta
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
import requests
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView, FormView
from django_otp import match_token, devices_for_user
from django_otp.forms import OTPAuthenticationForm
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.forms import (
    UserAddressForm,
    CardCreationForm,
    DepositCardForm,
    PaymentForm,
    StatementFilterForm,
    DepositApprovalForm,
    BudgetSystemForm,
    SignUpForm,
)
from accounts.models import UserAddress, Card, Payment, BudgetSystem
from accounts.tasks import count_monthly_budget
import logging

from accounts.utils import convert_currency

logger = logging.getLogger(__name__)


class SignUpView(View):
    form_class = SignUpForm
    template_name = "commons/signup.html"

    def get_user_totp_device(self, user, confirmed=None):
        devices = devices_for_user(user, confirmed=confirmed)
        for device in devices:
            if isinstance(device, TOTPDevice):
                return device

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # Deactivate account till it is confirmed
            user.save()
            device = self.get_user_totp_device(user)
            if not device:
                device = user.totpdevice_set.create(confirmed=True)
                print(device.config_url)
            current_site = get_current_site(request)
            mail_subject = "DJANGO OTP DEMO"
            message = render_to_string(
                "emails/account_activation_email.html",
                {
                    "user": user,
                    "qr_code": device.config_url,
                },
            )
            to_email = form.cleaned_data.get("email")
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.content_subtype = "html"
            email.send()

            messages.success(
                request, "Please Confirm your email to complete registration."
            )

            return redirect("login")

        return render(request, self.template_name, {"form": form})


class AccountLoginView(LoginView):
    template_name = "commons/login.html"
    form_class = OTPAuthenticationForm
    redirect_authenticated_user = True

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        # Let the custom authentication form handle authentication
        user = form.get_user()

        if user is not None:
            otp_token = form.cleaned_data.get("otp_token")
            device_match = match_token(user=user, token=otp_token)

            if device_match:
                # Log the user in
                login(self.request, user)
                return super().form_valid(form)
            else:
                # Handle token mismatch
                form.add_error("otp_token", "Invalid OTP token")
        else:
            # Handle authentication failure
            form.add_error(None, "Invalid email or password")

        return super().form_valid(form)


class LogoutView(RedirectView):
    pattern_name = "home"

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)


class UserProfileView(TemplateView):
    template_name = "accounts/user_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_staff:
            return redirect("accounts:staff_profile")
        context["user_profile_exists"] = True

        try:
            user_address = UserAddress.objects.get(user=user)
            context["address"] = user_address
        except UserAddress.DoesNotExist:
            context["address"] = None

        return context


class EditUserAddressView(LoginRequiredMixin, FormView):
    template_name = "accounts/edit_user_address.html"
    form_class = UserAddressForm
    success_url = reverse_lazy("accounts:user_profile")

    def form_valid(self, form):
        user = self.request.user

        try:
            user_address = UserAddress.objects.get(user=user)
            form = UserAddressForm(self.request.POST, instance=user_address)
        except UserAddress.DoesNotExist:
            form = UserAddressForm(self.request.POST)

        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            messages.success(self.request, "Address successfully updated.")
            return super().form_valid(form)

        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get(self, request, *args, **kwargs):
        user = request.user

        try:
            user_address = UserAddress.objects.get(user=user)
            form = UserAddressForm(instance=user_address)
        except UserAddress.DoesNotExist:
            form = UserAddressForm()

        return render(request, self.template_name, {"form": form})


def get_usd_exchange_rate():
    url = "https://belarusbank.by/api/kursExchange"

    # Отправка GET-запроса к API
    response = requests.get(url)

    # Проверка успешности запроса
    if response.status_code == 200:
        data = response.json()

        # Предположим, что "USD_in" находится внутри первого элемента списка
        if isinstance(data, list) and len(data) > 0:
            usd_in_rate = data[0].get("USD_in")
            return usd_in_rate
        else:
            print("Структура данных не соответствует ожидаемой.")
            return None
    else:
        # Вывод сообщения об ошибке в случае неудачного запроса
        print(f"Ошибка при получении данных. Статус код: {response.status_code}")
        return None


@login_required()
def make_payment(request, card_id=None):
    card = get_object_or_404(Card, id=card_id) if card_id else 1

    if request.method == "POST":
        form = PaymentForm(request.user, request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            selected_card = form.cleaned_data["card"]

            # Извлекаем card_type из выбранной карты
            card_type = selected_card.card_type
            if selected_card.currency == "U":
                usd_in_rate = get_usd_exchange_rate()

                # Пример значения по умолчанию, если запрос к API неудачен
                if usd_in_rate is None:
                    usd_in_rate = 3.116
                print(usd_in_rate)
                converted_amount = convert_currency(amount, "USD", "BYN", usd_in_rate)

            else:
                converted_amount = amount

            # Выполняем платеж
            success, message = selected_card.make_payment(converted_amount, card_type)

            if success:
                messages.success(request, f"{message}")
                return redirect("accounts:make_payment")
            else:
                messages.error(request, f"{message}")
                return redirect("accounts:make_payment")

    else:
        form = PaymentForm(request.user)

    return render(request, "accounts/payment_form.html", {"form": form, "card": card})


class StaffProfileView(TemplateView):
    template_name = "accounts/staff_profile.html"


class CardCreateView(LoginRequiredMixin, View):
    template_name = "accounts/create_card.html"
    success_url = "accounts:card_list"

    def get(self, request):
        form = CardCreationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        try:
            form = CardCreationForm(request.POST)
            if form.is_valid():
                card = form.save(commit=False)
                card.user = request.user
                card.save()
                logger.warning("Card creation successful")
                return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error during card creation: {str(e)}")

            raise
        return render(request, self.template_name, {"form": form})


class CardListView(LoginRequiredMixin, View):
    template_name = "accounts/card_list.html"

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            if not user.has_cards():
                return render(request, "accounts/no_cards.html")
            cards = user.user_cards.all()
            return render(request, self.template_name, {"cards": cards})
        else:
            return render(request, "accounts/no_cards.html")


@login_required
def deposit_card(request, card_id):
    card = Card.objects.get(id=card_id)

    if card.deposit_pending:
        messages.success(
            request, "You alrealy have pending deposit. Awaiting admin approval."
        )
        return redirect("accounts:card_list")

    if request.method == "POST":
        form = DepositCardForm(request.POST)
        if form.is_valid():
            deposit_amount = form.cleaned_data["deposit_amount"]

            # Set the pending deposit amount instead of updating the balance directly
            card.pending_deposit_amount += deposit_amount
            card.deposit_pending = True
            card.save()
            Payment.objects.create(
                card=card,
                amount=card.pending_deposit_amount,
                currency="B",
                card_type=card.card_type,
                deposit_pending=True,
            )

            # Redirect to a success page or wherever needed
            messages.success(
                request, "Deposit request submitted. Awaiting admin approval."
            )
            return redirect("accounts:card_list")
    else:
        form = DepositCardForm()

    return render(request, "accounts/deposit_form.html", {"form": form, "card": card})


@staff_member_required
def deposit_approval_list(request):
    pending_deposit_cards = Card.objects.filter(deposit_pending=True)
    return render(
        request,
        "accounts/deposit_approval_list.html",
        {"pending_deposit_cards": pending_deposit_cards},
    )


@staff_member_required
def deposit_approval(request, card_id):
    card = get_object_or_404(Card, id=card_id)

    if request.method == "POST":
        form = DepositApprovalForm(request.POST)
        if form.is_valid():
            approved = form.cleaned_data["approved"]

            if approved:
                # Process the approved deposit
                card.balance += card.pending_deposit_amount
                card.pending_deposit_amount = 0
                card.deposit_pending = False
                card.save()

                messages.success(
                    request, f"Deposit request for Card {card.account_no} approved."
                )
            else:
                # Reject the deposit
                card.pending_deposit_amount = 0
                card.deposit_pending = False
                card.save()

                messages.warning(
                    request, f"Deposit request for Card {card.account_no} rejected."
                )

            return redirect("accounts:deposit_approval_list")

    else:
        form = DepositApprovalForm()

    return render(
        request, "accounts/deposit_approval_form.html", {"form": form, "card": card}
    )


@login_required
def statement(request, card_id):
    form = StatementFilterForm(request.GET or None)
    card = Card.objects.get(id=card_id)

    if form.is_valid():
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"] + timedelta(days=1)

        payments = Payment.objects.filter(
            card=card, timestamp__range=[start_date, end_date]
        )

        # Separate payments and pending deposits
        regular_payments = payments.filter(deposit_pending=False)
        pending_deposits = payments.filter(deposit_pending=True)

        total_spent = regular_payments.aggregate(Sum("amount"))["amount__sum"] or 0
    else:
        regular_payments = []
        pending_deposits = []
        total_spent = 0

    return render(
        request,
        "accounts/statement.html",
        {
            "form": form,
            "regular_payments": regular_payments,
            "pending_deposits": pending_deposits,
            "total_spent": total_spent,
            "card": card,
        },
    )


# ----------------Budgeting Systems-----------------------


@login_required
def create_budgeting_system(request):
    user = request.user
    if request.method == "POST":
        form = BudgetSystemForm(request.user, request.POST)
        form.instance.user = user
        print(form.data)
        if form.is_valid():
            form.save()
            print(form.cleaned_data)
            card = Card.objects.filter(id=int(form.data["card"]), user=user).first()
            card.using_system = True
            card.daily_balance = card.balance / 30
            card.save()
            count_monthly_budget(int(form.data["card"]))
            return redirect("accounts:budgeting_systems_list")
        else:
            print(form.errors)
    else:
        form = BudgetSystemForm(request.user)

    return render(request, "accounts/create_budgeting_system.html", {"form": form})


@login_required
def budgeting_systems_list(request):
    user = request.user
    active_systems = BudgetSystem.objects.filter(user=user)

    context = {
        "active_budgeting_systems": active_systems,
    }

    return render(request, "accounts/budgeting_systems_list.html", context)


@login_required
def delete_budgeting_system(request, budgeting_system_id):
    system = get_object_or_404(BudgetSystem, id=budgeting_system_id)

    if request.method == "POST":
        system.delete()
        messages.success(request, f"Budgeting system was successfully deleted!.")
        return redirect("accounts:budgeting_systems_list")

    return render(request, "accounts/delete_budgeting_system.html", {"system": system})
