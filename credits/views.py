from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from accounts.models import Card
from credits.forms import CreditApprovalForm, CreditApplicationForm
from credits.models import CreditApplication, Credit


@staff_member_required
def credit_list(request):
    credit_applications = CreditApplication.objects.all()
    return render(
        request,
        "credits/credit_list.html",
        {"credit_applications": credit_applications},
    )


@login_required
def apply_credit(request):
    if request.method == "POST":
        form = CreditApplicationForm(request.POST)
        if form.is_valid():
            credit_application = form.save(commit=False)

            credit_application.user = (
                request.user._wrapped
                if hasattr(request.user, "_wrapped")
                else request.user
            )
            credit_application.status = "PENDING"
            credit_application.save()

            messages.success(
                request, "Credit application submitted. Awaiting approval."
            )
            return redirect("accounts:user_profile")
    else:
        form = CreditApplicationForm()

    return render(request, "credits/credit_application_form.html", {"form": form})


@staff_member_required
def approve_credit(request, credit_app_id):
    credit_application = get_object_or_404(CreditApplication, id=credit_app_id)

    if request.method == "POST":
        form = CreditApprovalForm(request.POST)
        if form.is_valid():
            approved = form.cleaned_data["approved"]

            if approved:
                # Process the approved credits application
                Credit.objects.create(
                    user=credit_application.user,
                    amount=credit_application.amount,
                    interest_rate=5.0,
                    term_months=12,
                    monthly_payment=calculate_monthly_payment(
                        credit_application.amount
                    ),
                    remaining_amount=credit_application.amount,
                    status="APPROVED",
                )
                if Card.objects.filter(
                    user=credit_application.user,
                    card_name=f"Credit: {credit_application.purpose}",
                ).exists():
                    raise ValidationError("Card already exists for this Credit")

                # Create associated card
                Card.objects.create(
                    card_name=f"{credit_application.purpose} Credit",
                    user=credit_application.user,
                    card_type="C",
                    balance=credit_application.amount,
                    currency="B",
                )

                messages.success(
                    request, "Credit and card created. Review and confirm to proceed."
                )

                credit_application.status = "APPROVED"
                credit_application.save()

                messages.success(request, f"Credit application approved.")
            else:
                # Reject the credits application
                credit_application.status = "REJECTED"
                credit_application.save()

                messages.warning(request, f"Credit application rejected.")

            return redirect("credits:credit_list")

    else:
        form = CreditApprovalForm()

    return render(
        request,
        "credits/credit_approval_form.html",
        {"form": form, "credit_application": credit_application},
    )


def calculate_monthly_payment(loan_amount):
    interest_rate = Decimal("0.05")
    term_months = Decimal("12")

    monthly_interest_rate = interest_rate / Decimal("12")
    monthly_payment = (loan_amount * monthly_interest_rate) / (
        Decimal("1") - (Decimal("1") + monthly_interest_rate) ** -term_months
    )

    return round(monthly_payment, 2)


@login_required
def active_credits(request):
    user_credits = Credit.objects.filter(user=request.user, status="APPROVED")
    return render(
        request, "credits/active_credits.html", {"user_credits": user_credits}
    )
