from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from decimal import Decimal
from credits.models import CreditApplication, Credit
from credits.views import calculate_monthly_payment


class CreditsTestCase(TestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email="testuser@gmail.com", password="testpass"
        )

    def test_credit_list_view(self):
        # Тестируем страницу со списком кредитных заявок
        response = self.client.get(reverse("credits:credit_list"))
        self.assertEqual(response.status_code, 302)

    def test_apply_credit_view(self):
        # Тестируем страницу подачи заявки на кредит
        response = self.client.get(reverse("credits:apply_credit"))
        self.assertEqual(response.status_code, 302)

    def test_apply_credit_view_post(self):
        # Тестируем подачу заявки на кредит (POST-запрос)
        data = {
            "amount": 1000,
            "purpose": "Home improvement",
        }
        self.client.login(email="testuser@gmail.com", password="testpass")
        response = self.client.post(reverse("credits:apply_credit"), data)
        self.assertEqual(response.status_code, 302)

    def test_approve_credit_view_post_approval(self):
        # Тестируем одобрение кредитной заявки (POST-запрос)
        credit_application = CreditApplication.objects.create(
            user=self.user, amount=1000, status="PENDING"
        )
        data = {"approved": True}  # Одобряем кредитную заявку
        response = self.client.post(
            reverse("credits:approve_credit", args=[credit_application.id]), data
        )
        self.assertEqual(response.status_code, 302)

    def test_approve_credit_view_post_rejection(self):
        # Тестируем отклонение кредитной заявки (POST-запрос)
        credit_application = CreditApplication.objects.create(
            user=self.user, amount=1000, status="PENDING"
        )
        data = {"approved": False}  # Отклоняем кредитную заявку
        response = self.client.post(
            reverse("credits:approve_credit", args=[credit_application.id]), data
        )
        self.assertEqual(
            response.status_code, 302
        )  # Ожидаем редирект после успешного отклонения

    def test_calculate_monthly_payment(self):
        # Тестируем функцию расчета ежемесячного платежа
        loan_amount = Decimal("1000")
        expected_monthly_payment = calculate_monthly_payment(loan_amount)
        self.assertAlmostEqual(expected_monthly_payment, Decimal("85.61"), places=2)

    def test_active_credits_view(self):
        # Тестируем страницу с активными кредитами пользователя
        Credit.objects.create(
            user=self.user,
            amount=1000,
            interest_rate=5.0,
            term_months=12,
            monthly_payment=86.61,
            remaining_amount=1000,
            status="APPROVED",
        )
        response = self.client.get(reverse("credits:active_credits"))
        self.assertEqual(response.status_code, 302)
