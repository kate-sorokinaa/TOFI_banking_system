from django.contrib import admin

from .models import User, UserAddress, Card, Payment, BudgetSystem

admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(Card)
admin.site.register(Payment)
admin.site.register(BudgetSystem)
