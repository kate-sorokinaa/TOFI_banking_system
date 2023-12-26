from django import forms

from accounts.models import Card


class FundTransferForm(forms.Form):
    card = forms.ModelChoiceField(
        queryset=None, empty_label="Select Card", label="Select Card"
    )
    receiver_account_number = forms.CharField(label="Receiver Account Number")
    amount = forms.DecimalField(label="Amount", max_digits=12, decimal_places=2)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_cards = Card.objects.filter(user=user)
        self.fields["card"].queryset = user_cards


class FundTransferByCardForm(forms.Form):
    card_one = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select Card",
        label="Select Card",
        widget=forms.Select,
    )
    card_two = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select Card",
        label="Select Card",
        widget=forms.Select,
    )
    amount = forms.DecimalField(label="Amount", max_digits=12, decimal_places=2)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_cards = Card.objects.filter(user=user)
        self.fields["card_one"].queryset = user_cards
        self.fields["card_two"].queryset = user_cards
