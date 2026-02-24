# utils.py
from .models import Notification, DocumentLog


def notify_user(user, document, message):
    Notification.objects.create(recipient=user, document=document, message=message)


def log_action(document, user, action, notes=''):
    DocumentLog.objects.create(document=document, user=user, action=action, notes=notes)
