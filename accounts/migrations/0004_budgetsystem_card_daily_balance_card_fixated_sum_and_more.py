# Generated by Django 4.2.7 on 2023-12-20 13:31

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        (
            "accounts",
            "0003_delete_userbankaccount_savingsgoal_user_payment_card_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="BudgetSystem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=150)),
                ("description", models.CharField(max_length=300)),
                ("daily_control", models.BooleanField(default=False)),
                (
                    "daily_percent",
                    models.PositiveIntegerField(
                        default=3,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
                ("daily_redirect", models.BooleanField(default=False)),
                ("redirect_savings", models.BooleanField(default=False)),
                (
                    "savings_percent",
                    models.PositiveIntegerField(
                        default=30,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="card",
            name="daily_balance",
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="card",
            name="fixated_sum",
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="card",
            name="using_system",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="card",
            name="card_name",
            field=models.CharField(default="New Card", max_length=100),
        ),
        migrations.DeleteModel(
            name="SavingsGoal",
        ),
        migrations.AddField(
            model_name="budgetsystem",
            name="card",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="card",
                to="accounts.card",
            ),
        ),
        migrations.AddField(
            model_name="budgetsystem",
            name="savings_card",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="savings_card",
                to="accounts.card",
            ),
        ),
        migrations.AddField(
            model_name="budgetsystem",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
