# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import User

@shared_task
def send_welcome_email(user_id):
    try:
        user = User.objects.get(id=user_id)
        
        # Définir le contenu selon le rôle
        if user.role == 'CLIENT':
            template_name = 'emails/welcome_client.html'
            subject = 'Welcome to DBD I&T - Your Trusted Interpretation Partner'
            context = {
                'name': user.username,
                'mission': 'Providing exceptional interpretation services',
                'values': [
                    'Integrity',
                    'Excellence',
                    'Cultural Sensitivity',
                    'Global Reach',
                    'Professionalism',
                    'Communication'
                ]
            }
        else:  # INTERPRETER
            template_name = 'emails/welcome_interpreter.html'
            subject = 'Welcome to DBD I&T - Join Our Interpreter Network'
            context = {
                'name': user.username,
                'benefits': [
                    'Flexible Schedule',
                    'Professional Development',
                    'Supportive Community',
                    'Remote Opportunities'
                ]
            }
        
        # Rendre le template HTML
        html_message = render_to_string(template_name, context)
        
        # Envoyer l'email
        send_mail(
            subject=subject,
            message='',  # Version texte plain (optionnelle)
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
    except User.DoesNotExist:
        print(f"User {user_id} not found")
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")