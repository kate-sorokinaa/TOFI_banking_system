from django.urls import path

from accounts.views import AccountLoginView
from credits.views import credit_list, apply_credit, approve_credit, active_credits

app_name = "credits"
urlpatterns = [
    path("login/", AccountLoginView.as_view(), name="login"),
    path("list/", credit_list, name="credit_list"),
    path("apply", apply_credit, name="apply_credit"),
    path("approve/<int:credit_app_id>/", approve_credit, name="approve_credit"),
    path("active_credits/", active_credits, name="active_credits"),
]
