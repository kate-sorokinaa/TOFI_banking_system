from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from accounts.models import Card, Payment
from accounts.views import get_usd_exchange_rate
from transactions.forms import FundTransferForm
from django.test import Client

User = get_user_model()


class FundTransferByCardViewTest(TestCase):
    def create_user(self, email="test@example.com", password="testpassword"):
        return User.objects.create_user(email=email, password=password)

    def setUp(self):
        # Создаем тестового пользователя и две карты
        self.user = self.create_user()
        self.card_one = Card.objects.create(
            user=self.user, balance=100, currency="U", card_type="D"
        )
        self.card_two = Card.objects.create(
            user=self.user, balance=0, currency="B", card_type="C"
        )

    def test_fund_transfer_view_get(self):
        response = self.client.get(
            reverse("transactions:fund_transfer_card_by_card"), follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_fund_transfer_by_card_view(self):
        # Входим в систему от имени пользователя
        self.client.login(email="test@example.com", password="testpassword")

        # Формируем URL и данные для передачи в представление
        url = reverse("transactions:fund_transfer_card_by_card")
        data = {
            "card_one": self.card_one.id,
            "card_two": self.card_two.id,
            "amount": 50,
        }

        # Отправляем POST-запрос на представление
        response = self.client.post(url, data)
        # Проверяем, что запрос был успешным (код ответа 302 - перенаправление)
        self.assertEqual(response.status_code, 302)

        # Получаем сообщения из контекста запроса
        messages = [m.message for m in get_messages(response.wsgi_request)]
        # Проверяем, что хотя бы одно сообщение содержит "Error"
        self.assertFalse(any("Error" in message for message in messages))

        # Проверяем, что балансы обновлены правильно
        sender_card = Card.objects.get(id=self.card_one.id)
        receiver_card = Card.objects.get(id=self.card_two.id)
        usd_in_rate = get_usd_exchange_rate()
        self.assertEqual(sender_card.balance, 50)
        self.assertAlmostEqual(
            Decimal(receiver_card.balance), 50 * Decimal(usd_in_rate), places=2
        )


class FundTransferViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass"
        )

        self.sender_card = Card.objects.create(
            user=self.user, card_type="C", currency="U", balance=100
        )
        self.receiver_card = Card.objects.create(
            user=self.user, card_type="D", currency="B", balance=50
        )

        self.client = Client()
        self.client.login(email="test@example.com", password="testpass")

    def test_fund_transfer_view_get(self):
        # Test GET request to the view
        response = self.client.get(reverse("transactions:fund_transfer"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/fund_transfer.html")
        self.assertIsInstance(response.context["form"], FundTransferForm)

    def test_fund_transfer_view_post_successful(self):
        data = {
            "receiver_account_number": self.receiver_card.account_no,
            "amount": 30,
            "card": self.sender_card.id,
        }
        response = self.client.post(reverse("transactions:fund_transfer"), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:card_list"))

        self.sender_card.refresh_from_db()
        self.receiver_card.refresh_from_db()
        self.assertAlmostEqual(float(self.sender_card.balance), float(70), places=2)
        usd_in_rate = get_usd_exchange_rate()
        self.assertAlmostEqual(
            float(self.receiver_card.balance),
            float(50 + Decimal("30") * Decimal(usd_in_rate)),
            places=2,
        )

        self.assertEqual(
            Payment.objects.filter(card=self.sender_card, amount=70).count(), 1
        )
        self.assertEqual(
            Payment.objects.filter(
                card=self.receiver_card,
                amount=50 + Decimal("30") * Decimal(usd_in_rate),
            ).count(),
            1,
        )

    def test_fund_transfer_view_post_insufficient_funds(self):
        data = {
            "receiver_account_number": self.receiver_card.account_no,
            "amount": 150,
            "card": self.sender_card.id,
        }
        response = self.client.post(reverse("transactions:fund_transfer"), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:card_list"))

        self.assertEqual(Payment.objects.count(), 2)
