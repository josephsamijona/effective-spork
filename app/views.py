# views.py
from django.views.generic import CreateView
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .forms import PublicQuoteRequestForm, ContactForm, ClientProfileUpdateForm, ClientRegistrationForm1, ClientRegistrationForm2,CustomPasswordResetForm,UserCreationForm, LoginForm,NotificationPreferencesForm
from .models import PublicQuoteRequest, ContactMessage
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, UpdateView, FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from app.models import NotificationPreference, Client, User
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from app.models import QuoteRequest, Assignment, Payment, Notification


class PublicQuoteRequestView(CreateView):
    model = PublicQuoteRequest
    form_class = PublicQuoteRequestForm
    template_name = 'public/quote_request_form.html'
    success_url = reverse_lazy('quote_request_success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Request a Quote'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        quote_request = self.object

        # Send confirmation email to customer
        customer_context = {
            'quote_request': quote_request,
            'name': quote_request.full_name,
        }
        customer_email_html = render_to_string('emails/quote_request_confirmation.html', customer_context)
        customer_email_txt = render_to_string('emails/quote_request_confirmation.txt', customer_context)

        send_mail(
            subject='Quote Request Received - DBD I&T',
            message=customer_email_txt,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[quote_request.email],
            html_message=customer_email_html,
            fail_silently=False,
        )

        # Send notification to staff
        staff_context = {
            'quote_request': quote_request,
            'admin_url': self.request.build_absolute_uri(
                reverse('admin:app_publicquoterequest_change', args=[quote_request.id])
            )
        }
        staff_email_html = render_to_string('emails/quote_request_notification.html', staff_context)
        staff_email_txt = render_to_string('emails/quote_request_notification.txt', staff_context)

        send_mail(
            subject=f'New Quote Request: {quote_request.company_name}',
            message=staff_email_txt,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.QUOTE_NOTIFICATION_EMAIL],
            html_message=staff_email_html,
            fail_silently=False,
        )

        messages.success(
            self.request,
            'Your quote request has been submitted successfully! '
            'We will contact you shortly with more information.'
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            'There was an error with your submission. Please check the form and try again.'
        )
        return super().form_invalid(form)

class QuoteRequestSuccessView(TemplateView):
    template_name = 'public/quote_request_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Quote Request Submitted'
        return context
    
    
class ContactView(CreateView):
    model = ContactMessage
    form_class = ContactForm
    template_name = 'public/contact.html'
    success_url = reverse_lazy('contact_success')

    def form_valid(self, form):
        response = super().form_valid(form)
        contact = self.object

        # Send confirmation email to the sender
        send_mail(
            subject='Thank you for contacting DBD I&T',
            message=f"""Dear {contact.name},

Thank you for contacting DBD I&T. We have received your message and will get back to you shortly.

Your message details:
Subject: {contact.subject}
Reference Number: #{contact.id}

Best regards,
DBD I&T Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contact.email],
            fail_silently=False,
        )

        # Send notification to staff
        send_mail(
            subject=f'New Contact Form Submission: {contact.subject}',
            message=f"""New contact form submission received:

From: {contact.name} <{contact.email}>
Subject: {contact.subject}

Message:
{contact.message}

View in admin panel: {self.request.build_absolute_uri(reverse('admin:app_contactmessage_change', args=[contact.id]))}""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_NOTIFICATION_EMAIL],
            fail_silently=False,
        )

        messages.success(
            self.request,
            'Your message has been sent successfully! We will contact you shortly.'
        )
        return response

class ContactSuccessView(TemplateView):
    template_name = 'public/contact_success.html'
    
    
#################################CLIENT##################33
# views.py


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.role == 'CLIENT':
            return reverse_lazy('client_dashboard')
        return reverse_lazy('interpreter_dashboard')

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid email or password.')
        return super().form_invalid(form)

@method_decorator(never_cache, name='dispatch')
class ClientRegistrationView(FormView):
    template_name = 'accounts/registration/step1.html'
    form_class = ClientRegistrationForm1
    success_url = reverse_lazy('client_registration_step2')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('client_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Store step 1 data in session
        self.request.session['registration_step1'] = {
            'email': form.cleaned_data['email'],
            'password': form.cleaned_data['password1'],
            'first_name': form.cleaned_data['first_name'],
            'last_name': form.cleaned_data['last_name'],
            'phone': form.cleaned_data['phone']
        }
        return super().form_valid(form)

@method_decorator(never_cache, name='dispatch')
class ClientRegistrationStep2View(FormView):
    template_name = 'accounts/registration/step2.html'
    form_class = ClientRegistrationForm2
    success_url = reverse_lazy('client_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('registration_step1'):
            return redirect('client_registration')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        step1_data = self.request.session['registration_step1']
        
        # Create user
        user = User.objects.create_user(
            email=step1_data['email'],
            password=step1_data['password'],
            first_name=step1_data['first_name'],
            last_name=step1_data['last_name'],
            phone=step1_data['phone'],
            role='CLIENT'
        )

        # Create client profile
        client = form.save(commit=False)
        client.user = user
        client.save()

        # Clean up session
        del self.request.session['registration_step1']

        # Log the user in
        login(self.request, user)
        messages.success(self.request, 'Your account has been created successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class ClientProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientProfileUpdateForm
    template_name = 'accounts/profile/update.html'
    success_url = reverse_lazy('client_dashboard')

    def get_object(self, queryset=None):
        return self.request.user.client_profile

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)

class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
    model = NotificationPreference
    form_class = NotificationPreferencesForm
    template_name = 'accounts/profile/notifications.html'
    success_url = reverse_lazy('client_dashboard')

    def get_object(self, queryset=None):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

    def form_valid(self, form):
        messages.success(self.request, 'Your notification preferences have been updated!')
        return super().form_valid(form)

class RegistrationSuccessView(TemplateView):
    template_name = 'accounts/registration/success.html'
    
    
# views.py


class ClientDashboardView(LoginRequiredMixin, UserPassesTestMixin):
    template_name = 'dashboard/client_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'CLIENT'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer le client
        client = self.request.user.client_profile
        
        # Période pour les statistiques (30 derniers jours)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Statistiques de base
        context['stats'] = {
            'pending_quotes': QuoteRequest.objects.filter(
                client=client, 
                status='PENDING'
            ).count(),
            'active_assignments': Assignment.objects.filter(
                client=client, 
                status__in=['CONFIRMED', 'IN_PROGRESS']
            ).count(),
            'completed_assignments': Assignment.objects.filter(
                client=client, 
                status='COMPLETED', 
                completed_at__gte=thirty_days_ago
            ).count(),
            'total_spent': Payment.objects.filter(
                assignment__client=client,
                status='COMPLETED',
                payment_date__gte=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or 0
        }
        
        # Dernières demandes de devis
        context['recent_quotes'] = QuoteRequest.objects.filter(
            client=client
        ).order_by('-created_at')[:5]
        
        # Missions à venir
        context['upcoming_assignments'] = Assignment.objects.filter(
            client=client,
            status__in=['CONFIRMED', 'IN_PROGRESS'],
            start_time__gte=timezone.now()
        ).order_by('start_time')[:5]
        
        # Derniers paiements
        context['recent_payments'] = Payment.objects.filter(
            assignment__client=client
        ).order_by('-payment_date')[:5]
        
        # Notifications non lues
        context['unread_notifications'] = Notification.objects.filter(
            recipient=self.request.user,
            read=False
        ).order_by('-created_at')[:5]
        
        return context







































































































#####INTERPRETERDASHBOARD
class InterpreterDashboardView(LoginRequiredMixin, UserPassesTestMixin):
    template_name = 'dashboard/interpreter_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer l'interprète
        interpreter = self.request.user.interpreter_profile
        
        # Période pour les statistiques
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Statistiques générales
        context['stats'] = {
            'pending_assignments': Assignment.objects.filter(
                interpreter=interpreter, 
                status='PENDING'
            ).count(),
            'upcoming_assignments': Assignment.objects.filter(
                interpreter=interpreter,
                status='CONFIRMED',
                start_time__gte=timezone.now()
            ).count(),
            'completed_assignments': Assignment.objects.filter(
                interpreter=interpreter,
                status='COMPLETED',
                completed_at__gte=thirty_days_ago
            ).count(),
            'total_earnings': Payment.objects.filter(
                assignment__interpreter=interpreter,
                payment_type='INTERPRETER_PAYMENT',
                status='COMPLETED',
                payment_date__gte=thirty_days_ago
            ).aggregate(total=Sum('amount'))['total'] or 0
        }
        
        # Missions du jour
        today = timezone.now().date()
        context['today_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            start_time__date=today,
            status__in=['CONFIRMED', 'IN_PROGRESS']
        ).order_by('start_time')
        
        # Prochaines missions
        context['upcoming_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='CONFIRMED',
            start_time__gt=timezone.now()
        ).order_by('start_time')[:5]
        
        # Derniers paiements
        context['recent_payments'] = Payment.objects.filter(
            assignment__interpreter=interpreter,
            payment_type='INTERPRETER_PAYMENT'
        ).order_by('-payment_date')[:5]
        
        # Notifications non lues
        context['unread_notifications'] = Notification.objects.filter(
            recipient=self.request.user,
            read=False
        ).order_by('-created_at')[:5]
        
        # Statistiques de performance
        assignments_completed = Assignment.objects.filter(
            interpreter=interpreter,
            status='COMPLETED'
        )
        
        context['performance'] = {
            'total_hours': sum((a.end_time - a.start_time).total_seconds() / 3600 
                             for a in assignments_completed),
            'average_rating': assignments_completed.aggregate(
                avg_rating=Avg('assignmentfeedback__rating')
            )['avg_rating'] or 0,
            'completion_rate': (
                assignments_completed.count() / 
                Assignment.objects.filter(interpreter=interpreter).count() * 100
                if Assignment.objects.filter(interpreter=interpreter).exists() 
                else 0
            )
        }
        
        return context