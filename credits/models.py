from django.db import models

from accounts.models import User
from credits.constants import CREDIT_STATUS, STATUS


class CreditApplication(models.Model):
    user = models.ForeignKey(
        User,
        related_name="user_credit_application",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=CREDIT_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)


class Credit(models.Model):
    user = models.ForeignKey(
        User,
        related_name="user_credit",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.PositiveIntegerField()
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
