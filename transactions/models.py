from django.db import models

from accounts.models import Card


class Transaction(models.Model):
    sender_card = models.ForeignKey(
        Card, on_delete=models.CASCADE, related_name="sent_transactions", default=None
    )
    receiver_card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name="received_transactions",
        default=None,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender_card} -> {self.receiver_card}: {self.amount} BYN"
