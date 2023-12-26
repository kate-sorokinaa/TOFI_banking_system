from django.urls import path
from .views import (
    LogoutView,
    UserProfileView,
    CardCreateView,
    CardListView,
    deposit_card,
    StaffProfileView,
    make_payment,
    statement,
    deposit_approval,
    deposit_approval_list,
    create_budgeting_system,
    budgeting_systems_list,
    delete_budgeting_system,
    EditUserAddressView,
    AccountLoginView,
)

app_name = "accounts"

urlpatterns = [
    path("login/", AccountLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="user_logout"),
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    path("profile-edit/", EditUserAddressView.as_view(), name="edit_profile"),
    path("staff_profile/", StaffProfileView.as_view(), name="staff_profile"),
    path("make_payment/", make_payment, name="make_payment"),
    path("create_card/", CardCreateView.as_view(), name="create_card"),
    path("card_list/", CardListView.as_view(), name="card_list"),
    path("card_history/<int:card_id>", statement, name="card_history"),
    path("deposit_card/<int:card_id>", deposit_card, name="deposit_form"),
    path("deposit-approval/", deposit_approval_list, name="deposit_approval_list"),
    path("deposit-approval/<int:card_id>/", deposit_approval, name="deposit_approval"),
    path(
        "budgeting-system/create/",
        create_budgeting_system,
        name="create_budgeting_system",
    ),
    path(
        "budgeting-systems-list/", budgeting_systems_list, name="budgeting_systems_list"
    ),
    path(
        "delete-budgeting-system/<int:budgeting_system_id>/",
        delete_budgeting_system,
        name="delete_budgeting_system",
    ),
]
