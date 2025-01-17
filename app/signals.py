# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from .tasks import send_welcome_email
from django.db import models
from .models import QuoteRequest
from .tasks import send_quote_request_status_email

@receiver(post_save, sender=QuoteRequest)
def handle_quote_request_status_change(sender, instance, created, **kwargs):
    # Envoyer l'email pour une nouvelle demande ou un changement de statut
    if created or instance.status != instance._original_status:
        send_quote_request_status_email.delay(instance.id)

# Add this method to your QuoteRequest model
class QuoteRequest(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._original_status = self.status





@receiver(post_save, sender=User)
def send_welcome_email_on_creation(sender, instance, created, **kwargs):
    if created:  # Uniquement lors de la création
        send_welcome_email.delay(instance.id)