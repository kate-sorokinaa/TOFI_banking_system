from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Card
from accounts.utils import convert_currency

User = get_user_model()


class CardModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.card_data = {
            "user": self.user,
            "card_name": "Test Card",
            "account_no": "1234567890123456",
            "balance": 1000.00,
            "cvv_code": "123",
            "card_type": "C",
            "currency": "B",
        }
        self.card = Card.objects.create(**self.card_data)

    def test_card_creation(self):
        self.assertEqual(Card.objects.count(), 1)
        card = Card.objects.get(user=self.user)
        self.assertEqual(card.card_name, "Test Card")

    def test_make_payment_credit_card(self):
        # Проверка, что начальный баланс установлен правильно
        self.assertEqual(self.card.balance, 1000.00)

        # Проведение платежа с кредитной карты
        success, message = self.card.make_payment(500.00, "C")

        # Проверка успешности платежа
        self.assertTrue(success)
        self.assertEqual(message, "Payment successful")

        # Проверка обновления баланса карты
        self.assertEqual(self.card.balance, 500.00)

    def test_make_payment_invalid_card_type(self):
        # Попытка проведения платежа с недопустимым типом карты
        success, message = self.card.make_payment(500.00, "X")

        # Проверка неуспешности платежа и соответствующего сообщения
        self.assertFalse(success)
        self.assertEqual(message, "Invalid card type")

    def test_make_payment_conversion(self):
        # Тестирование правильной конвертации валют при выполнении платежа

        amount = 100
        from_currency = "USD"
        to_currency = "BYN"
        rate = 3.116

        # Вызов функции конвертации
        converted_amount = convert_currency(amount, from_currency, to_currency, rate)

        # Проверка, что конвертация произошла корректно
        self.assertAlmostEqual(
            converted_amount, Decimal(str((amount / rate))), places=2
        )


class ChangePasswordViewTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser",
            "password": "testpassword123",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.login_url = reverse("login")
        self.change_password_url = reverse("change_password")

    def test_change_password_view_authenticated(self):
        # Проверка, что пользователь авторизован
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.change_password_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "commons/password_change.html")


class CardCreateViewTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser",
            "password": "testpassword123",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.login_url = reverse("login")
        self.create_card_url = reverse("accounts:create_card")

    def test_create_card_view_authenticated(self):
        # Проверка, что пользователь авторизован
        self.client.login(username="testuser", password="testpassword123")
        response = self.client.get(self.create_card_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/create_card.html")

    def test_create_card_view_unauthenticated(self):
        response = self.client.get(reverse("accounts:create_card"))

        # Проверяем, что пользователь перенаправлен на страницу входа
        self.assertRedirects(
            response,
            reverse("accounts:login") + "?next=" + reverse("accounts:create_card"),
        )

        if response.status_code == 302:
            pass
        else:
            self.assertTemplateUsed(response, "accounts/create_card.html")


class CardListViewTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpassword",
        }
        self.login_url = reverse("login")
        self.user = User.objects.create_user(**self.user_data)
        self.card = Card.objects.create(user=self.user, balance=100.0)

    def test_card_list_view_authenticated_with_cards(self):
        self.client.login(email="testuser@example.com", password="testpassword")
        response = self.client.get(reverse("accounts:card_list"))
        self.assertTemplateUsed(response, "accounts/card_list.html")

    def test_card_list_view_authenticated_without_cards(self):
        self.client.login(email="testuser@example.com", password="testpassword")
        self.card.delete()
        response = self.client.get(reverse("accounts:card_list"))
        self.assertEqual(response.status_code, 200)

    def test_card_list_view_unauthenticated(self):
        response = self.client.get(reverse("accounts:card_list"))

        # Проверяем, что пользователь перенаправлен на страницу входа
        self.assertRedirects(
            response,
            reverse("accounts:login") + "?next=" + reverse("accounts:card_list"),
        )

        if response.status_code == 302:
            pass
        else:
            # Если это не перенаправление, проверяем использование шаблона
            self.assertTemplateUsed(response, "accounts/no_cards.html")


class DepositCardViewTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser",
            "password": "testpassword123",
        }
        self.login_url = reverse("login")
        self.user = User.objects.create_user(**self.user_data)
        self.card = Card.objects.create(
            user=self.user, balance=100.0, deposit_pending=False
        )


class DepositApprovalListViewTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser",
            "password": "testpassword123",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.staff_user = User.objects.create_user(
            email="staffuser@example.com", password="staffpassword", is_staff=True
        )

    def test_deposit_approval_list_view_authenticated_staff(self):
        self.client.login(email="staffuser@example.com", password="staffpassword")
        response = self.client.get(reverse("accounts:deposit_approval_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/deposit_approval_list.html")

    def test_deposit_approval_list_view_unauthenticated(self):
        response = self.client.get(reverse("accounts:deposit_approval_list"))
        self.assertRedirects(
            response, f'/admin/login/?next={reverse("accounts:deposit_approval_list")}'
        )


class DepositApprovalViewTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser",
            "password": "testpassword123",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.staff_user = User.objects.create_user(
            email="staffuser@example.com", password="staffpassword", is_staff=True
        )
        self.card = Card.objects.create(
            user=self.user,
            balance=100.0,
            deposit_pending=True,
            pending_deposit_amount=50.0,
        )

    def test_deposit_approval_view_authenticated_staff(self):
        self.client.login(email="staffuser@example.com", password="staffpassword")
        response = self.client.get(
            reverse("accounts:deposit_approval", args=[self.card.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/deposit_approval_form.html")
