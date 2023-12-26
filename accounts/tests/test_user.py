from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.models import Card, UserAddress

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(email="testuser@example.com")
        self.assertEqual(user.email, "testuser@example.com")
        self.assertTrue(user.check_password("testpassword123"))

    def test_has_cards_method(self):
        # Проверка, что у пользователя нет карточек по умолчанию
        self.assertFalse(self.user.has_cards())

        # Создание карточки для пользователя
        card_data = {
            "user": self.user,
            "card_name": "Test Card",
            "account_no": "1234567890123456",
            "balance": 1000.00,
            "cvv_code": "123",
            "card_type": "C",
            "currency": "B",
        }
        Card.objects.create(**card_data)

        self.assertTrue(self.user.has_cards())


class UserAddressModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpassword123",
        }
        self.user = User.objects.create_user(**self.user_data)
        self.address_data = {
            "user": self.user,
            "street_address": "123 Main St",
            "city": "Cityville",
            "postal_code": 12345,
            "country": "Countryland",
        }
        self.address = UserAddress.objects.create(**self.address_data)

    def test_address_creation(self):
        self.assertEqual(UserAddress.objects.count(), 1)
        address = UserAddress.objects.get(user=self.user)
        self.assertEqual(address.street_address, "123 Main St")


class EditUserAddressViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com", password="testpassword"
        )

    def test_edit_user_address_authenticated(self):
        # Авторизуем пользователя
        self.client.login(email="testuser@example.com", password="testpassword")

        address_data = {
            "street_address": "123 Main St",
            "city": "Cityville",
            "postal_code": "12345",
            "country": "Countryland",
        }
        user_address = UserAddress.objects.create(user=self.user, **address_data)

        # Отправляем GET-запрос на страницу редактирования адреса
        response = self.client.get(reverse("accounts:edit_profile"))

        self.assertEqual(response.status_code, 200)

        # Проверяем, что форма содержит данные адреса пользователя
        self.assertContains(response, user_address.street_address)
        self.assertContains(response, user_address.city)
        self.assertContains(response, user_address.postal_code)
        self.assertContains(response, user_address.country)

    def test_edit_user_address_unauthenticated(self):
        response = self.client.get(reverse("accounts:edit_profile"))

        # Проверяем, что пользователь перенаправлен на страницу входа
        expected_url = (
            reverse("accounts:login") + "?next=" + reverse("accounts:edit_profile")
        )
        self.assertRedirects(response, expected_url)
