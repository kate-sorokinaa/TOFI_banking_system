from django import forms

from credits.models import CreditApplication


class CreditApplicationForm(forms.ModelForm):
    class Meta:
        model = CreditApplication
        fields = ["amount", "purpose"]

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be a positive number.")
        return amount


class CreditApprovalForm(forms.Form):
    approved = forms.BooleanField(label="Approve credits", required=False)
