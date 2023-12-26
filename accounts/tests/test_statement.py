from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from accounts.models import Card, Payment, User


class StatementViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@gmail.com", password="testpass"
        )
        self.card = Card.objects.create(user=self.user, balance=1000)

    def test_statement_view_authenticated(self):
        self.client.login(email="testuser@gmail.com", password="testpass")

        # Добавляем платежи
        Payment.objects.create(
            card=self.card, amount=Decimal("50"), deposit_pending=False
        )
        Payment.objects.create(
            card=self.card, amount=Decimal("30"), deposit_pending=True
        )

        # Отправляем GET-запрос на страницу выписки
        response = self.client.get(
            reverse("accounts:card_history", kwargs={"card_id": self.card.id})
        )

        self.assertEqual(response.status_code, 200)

        # Проверяем, что используется правильный шаблон
        self.assertTemplateUsed(response, "accounts/statement.html")

        # Проверяем наличие данных в контексте
        self.assertIn("form", response.context)
        self.assertIn("regular_payments", response.context)
        self.assertIn("pending_deposits", response.context)
        self.assertIn("total_spent", response.context)
        self.assertIn("card", response.context)

        # Проверяем, что баланс карты передан правильно
        self.assertEqual(response.context["card"].balance, 1000)

    def test_statement_view_unauthenticated(self):
        response = self.client.get(
            reverse("accounts:card_history", kwargs={"card_id": self.card.id})
        )

        # Проверяем, что пользователь перенаправлен на страницу входа
        self.assertRedirects(
            response,
            "/accounts/login/?next="
            + reverse("accounts:card_history", kwargs={"card_id": self.card.id}),
        )
