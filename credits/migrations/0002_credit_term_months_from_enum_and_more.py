# Generated by Django 4.2.7 on 2023-12-26 03:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("credits", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="credit",
            name="term_months_from_enum",
            field=models.CharField(
                choices=[("6", "6 months"), ("12", "1 year"), ("24", "2 years")],
                default="6",
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="credit",
            name="interest_rate",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name="credit",
            name="term_months",
            field=models.PositiveIntegerField(default=1),
        ),
    ]