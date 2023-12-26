import random

from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.db import models, transaction

from .constants import CURRENCY, CARD_TYPE
from .managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, null=False, blank=False)
    objects = UserManager()

    USERNAME_FIELD = "email"
    is_active = models.BooleanField(
        default=True,
    )
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def has_cards(self):
        return self.user_cards.exists()


class UserAddress(models.Model):
    user = models.OneToOneField(
        User,
        related_name="user_address",
        on_delete=models.CASCADE,
    )
    street_address = models.CharField(max_length=512)
    city = models.CharField(max_length=256)
    postal_code = models.PositiveIntegerField()
    country = models.CharField(max_length=256)

    def __str__(self):
        return self.user.email


class Card(models.Model):
    card_name = models.CharField(max_length=100, default="New Card")
    using_system = models.BooleanField(default=False)
    account_no = models.CharField(max_length=16, unique=True)
    user = models.ForeignKey(
        User,
        related_name="user_cards",
        on_delete=models.CASCADE,
    )
    balance = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    daily_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.00)],
        default=0.00,
    )
    fixated_sum = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.00)],
        default=0.00,
    )
    pending_deposit_amount = models.DecimalField(
        default=0, max_digits=12, decimal_places=2
    )
    is_deposit_allowed = models.BooleanField(default=True)
    deposit_pending = models.BooleanField(default=False)
    cvv_code = models.CharField(max_length=3)
    card_type = models.CharField(max_length=1, choices=CARD_TYPE)
    currency = models.CharField(max_length=1, choices=CURRENCY)

    def save(self, *args, **kwargs):
        # Generate values for some fields
        if not self.account_no:
            self.account_no = "".join(str(random.randint(0, 9)) for _ in range(16))
        if not self.cvv_code:
            self.cvv_code = random.randint(100, 999)

        super().save(*args, **kwargs)

    def make_payment(self, amount, card_type):
        if card_type == "C":
            if not self.is_deposit_allowed:
                return False, "Deposit not allowed for credits card"
        elif card_type == "D":
            if self.using_system:
                if self.daily_balance < amount:
                    return (
                        False,
                        "Insufficient funds for debit card with daily budgeting system",
                    )
            else:
                if self.balance < amount:
                    return False, "Insufficient funds for debit card"
        else:
            return False, "Invalid card type"

        # Perform the payment transaction
        with transaction.atomic():
            # Create a Payment record
            Payment.objects.create(
                card=self,
                amount=amount,
                currency="B",
                card_type=card_type,
            )

            # Update the card balance
            self.balance -= amount
            if self.using_system:
                self.daily_balance -= amount
            self.save()

        return True, "Payment successful"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}- {self.card_name} {self.balance} {self.currency}"


class BudgetSystem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=300)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="card")
    savings_card = models.ForeignKey(
        Card, on_delete=models.DO_NOTHING, related_name="savings_card"
    )
    daily_control = models.BooleanField(default=False)
    daily_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)], default=3, null=True
    )
    daily_redirect = models.BooleanField(default=False)
    savings_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=30
    )

    def save(self, *args, **kwargs):
        if not self.savings_card:
            self.daily_redirect = False
            self.redirect_savings = False
        if not self.daily_control:
            self.daily_percent = None
            self.daily_redirect = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}: {self.description}"


class Payment(models.Model):
    card = models.ForeignKey(
        Card,
        related_name="card_payments",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=1, choices=CURRENCY)
    card_type = models.CharField(max_length=1, choices=CARD_TYPE)
    timestamp = models.DateTimeField(default=timezone.now)
    deposit_pending = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.card.id} - {self.amount} {self.currency} ({self.timestamp})"
