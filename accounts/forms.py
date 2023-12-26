from datetime import datetime, timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms import SelectDateWidget
from .models import User, UserAddress, Card, BudgetSystem
from .constants import GENDER_CHOICE, CARD_TYPE, CURRENCY

# Sign Up Form


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text="Optional")
    last_name = forms.CharField(max_length=30, required=False, help_text="Optional")
    email = forms.EmailField(max_length=254, help_text="Enter a valid email address")

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]


class UserAddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ["street_address", "city", "postal_code", "country"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    "class": (
                        "appearance-none block w-full bg-gray-200 "
                        "text-gray-700 border border-gray-200 rounded "
                        "py-3 px-4 leading-tight focus:outline-none "
                        "focus:bg-white focus:border-gray-500"
                    )
                }
            )


class UserRegistrationForm(UserCreationForm):
    gender = forms.ChoiceField(choices=GENDER_CHOICE)
    birth_date = forms.DateField()

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    "class": (
                        "appearance-none block w-full bg-gray-200 "
                        "text-gray-700 border border-gray-200 "
                        "rounded py-3 px-4 leading-tight "
                        "focus:outline-none focus:bg-white "
                        "focus:border-gray-500"
                    )
                }
            )

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)


class CardCreationForm(forms.ModelForm):
    card_name = forms.CharField()
    card_type = forms.ChoiceField(choices=CARD_TYPE)
    currency = forms.ChoiceField(choices=CURRENCY)

    class Meta:
        model = Card
        fields = [
            "card_name",
            "card_type",
            "currency",
        ]


class EmailVerificationForm(forms.Form):
    email = forms.EmailField(label="Email")
    verification_code = forms.CharField(label="Verification Code")


class DepositCardForm(forms.Form):
    deposit_amount = forms.DecimalField()


class PaymentForm(forms.Form):
    amount = forms.DecimalField(required=True)
    card = forms.ModelChoiceField(
        queryset=None, empty_label="Select Card", label="Select Card"
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_cards = Card.objects.filter(user=user)
        self.fields["card"].queryset = user_cards

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class CustomSelectDateWidget(SelectDateWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow selecting years that are more than 30 years in the past
        current_year = datetime.now().year
        self.years = range(current_year - 5, current_year + 1)


class StatementFilterForm(forms.Form):
    start_date = forms.DateField(
        widget=CustomSelectDateWidget(
            empty_label=("Choose Year", "Choose Month", "Choose Day")
        )
    )
    end_date = forms.DateField(
        widget=CustomSelectDateWidget(
            empty_label=("Choose Year", "Choose Month", "Choose Day")
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set the default end_date to today
        self.fields["end_date"].initial = datetime.now().date()

        # Set the default start_date to one month before the end_date
        default_start_date = self.fields["end_date"].initial - timedelta(days=30)
        self.fields["start_date"].initial = default_start_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # Ensure start_date is not after end_date
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date")

        return cleaned_data


class DepositApprovalForm(forms.Form):
    approved = forms.BooleanField(label="Approve deposit", required=False)


class BudgetSystemForm(forms.ModelForm):
    card = forms.ModelChoiceField(
        queryset=None, empty_label="Select Card", label="Select Card"
    )
    savings_card = forms.ModelChoiceField(
        queryset=None, empty_label="Select Savings Card", label="Select Savings Card"
    )
    daily_control = forms.BooleanField(label="Control daily", required=False)
    daily_redirect = forms.BooleanField(label="Redirect daily", required=False)

    class Meta:
        model = BudgetSystem
        fields = [
            "name",
            "description",
            "daily_percent",
            "savings_percent",
            "card",
            "savings_card",
            "daily_control",
            "daily_redirect",
        ]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_cards = Card.objects.filter(user=user)
        self.fields["card"].queryset = user_cards
        self.fields["savings_card"].queryset = user_cards
