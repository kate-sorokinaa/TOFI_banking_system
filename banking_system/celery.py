from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "banking_system.settings")

app = Celery("banking_system")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "check_credit_card_payments": {
        "task": "accounts.tasks.check_credit_card_payments",
        "schedule": crontab(day_of_month="1", hour="0"),  # Start every month
    },
    "calculate_interest": {
        "task": "calculate_interest",
        # http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html
        "schedule": crontab(day_of_month="1", hour="0"),
    },
    "process_pending_deposits": {
        "task": "accounts.tasks.process_pending_deposits",
        "schedule": 60,  # Set the schedule interval in seconds (e.g., every 10 minutes)
    },
    "recount_daily_budget": {
        "task": "accounts.tasks.recount_daily_budget",
        "schedule": crontab(
            minute="*/10"
        ),  # Set the schedule interval in seconds (e.g., every 10 minutes)
    },
    "count_monthly_budget_all": {
        "task": "accounts.tasks.count_monthly_budget_all",
        "schedule": crontab(
            minute="*/60"
        ),  # Set the schedule interval in seconds (e.g., every 10 minutes)
    },
}
