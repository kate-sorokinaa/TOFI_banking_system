"""banking_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import include, path

from accounts.views import AccountLoginView, SignUpView
from core.views import HomeView


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("admin/", admin.site.urls),
    path("transactions/", include("transactions.urls", namespace="transactions")),
    path("credits/", include("credits.urls", namespace="credits")),
    path("login/", AccountLoginView.as_view(), name="login"),
    path("signup/", SignUpView.as_view(), name="signup"),
    # Change Password
    path(
        "change-password/",
        PasswordChangeView.as_view(
            template_name="commons/password_change.html", success_url="/"
        ),
        name="change_password",
    ),
    # Forget Password
    path(
        "password-reset/",
        PasswordResetView.as_view(
            template_name="commons/password-reset/password_reset.html",
            subject_template_name="commons/password-reset/password_reset_subject.txt",
            success_url="/login/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(
            template_name="commons/password-reset/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="commons/password-reset/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        PasswordResetCompleteView.as_view(
            template_name="commons/password-reset/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
