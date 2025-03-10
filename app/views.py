# views.py

# Django core imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncYear
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from .models import NotificationPreference, Interpreter,Language
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

# Python standard library
from datetime import timedelta
from decimal import Decimal

# Local imports
from .forms import (
    AssignmentFeedbackForm,
    ClientProfileForm,
    ClientProfileUpdateForm,
    ClientRegistrationForm1,
    ClientRegistrationForm2,
    ContactForm,
    CustomPasswordChangeForm,
    CustomPasswordResetForm,
    CustomPasswordtradChangeForm,
    InterpreterProfileForm,
    InterpreterRegistrationForm1,
    InterpreterRegistrationForm2,
    InterpreterRegistrationForm3,
    LoginForm,
    NotificationPreferenceForm,
    NotificationPreferencesForm,
    PublicQuoteRequestForm,
    QuoteFilterForm,
    QuoteRequestForm,
    UserCreationForm,
    UserProfileForm,
)

from .models import (
    User,
    Assignment,
    Client,
    ContactMessage,
    Notification,
    NotificationPreference,
    Payment,
    PublicQuoteRequest,
    Quote,
    QuoteRequest,
    User,ServiceType,AssignmentNotification
)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .forms import InterpreterStatementForm, InterpreterServiceForm
from .models import InterpreterStatement, InterpreterService
import random
import string
from decimal import Decimal

import logging

logger = logging.getLogger(__name__)

###########################MAIN########################################
#######################################################################
#######################################################################
#######################################################################
#######################################################################
class ChooseRegistrationTypeView(TemplateView):
    template_name = 'choose_registration.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role == 'CLIENT':
                return redirect('dbdint:client_dashboard')
            return redirect('dbdint:interpreter_dashboard')
        return super().dispatch(request, *args, **kwargs)



class PublicQuoteRequestView(CreateView):
    model = PublicQuoteRequest
    form_class = PublicQuoteRequestForm
    template_name = 'public/quote_request_form.html'
    success_url = reverse_lazy('dbdint:quote_request_success')

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
                reverse('dbdint:app_publicquoterequest_change', args=[quote_request.id])
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
    success_url = reverse_lazy('dbdint:contact_success')

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
    



class CustomLoginView(LoginView):
    template_name = 'login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        logger.info(f"Determining success URL for user {user.id} with role {user.role}")
        
        try:
            if user.role == 'CLIENT':
                logger.debug(f"User {user.id} identified as CLIENT, redirecting to client dashboard")
                return reverse_lazy('dbdint:client_dashboard')
            
            logger.debug(f"User {user.id} identified as INTERPRETER, redirecting to interpreter dashboard")
            return reverse_lazy('dbdint:interpreter_dashboard')
            
        except Exception as e:
            logger.error(f"Error in get_success_url for user {user.id}: {str(e)}", exc_info=True)
            raise

    def form_invalid(self, form):
        logger.warning(
            "Login attempt failed",
            extra={
                'errors': form.errors,
                'cleaned_data': form.cleaned_data,
                'ip_address': self.request.META.get('REMOTE_ADDR')
            }
        )
        messages.error(self.request, 'Invalid email or password.')
        return super().form_invalid(form)

    def form_valid(self, form):
        logger.info(f"Successful login for user: {form.get_user().id}")
        return super().form_valid(form)
#################################CLIENT##################
#########################################################
####################################################################################################################################################
#########################################################
#########################################################



@method_decorator(never_cache, name='dispatch')
class ClientRegistrationView(FormView):
    template_name = 'client/auth/step1.html'
    form_class = ClientRegistrationForm1
    success_url = reverse_lazy('dbdint:client_register_step2')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.registration_complete:
            return redirect('dbdint:client_dashboard')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            logger.info("Processing valid registration form step 1")
            
            # Créer l'utilisateur avec le rôle CLIENT
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone=form.cleaned_data['phone'],
                role=User.Roles.CLIENT,
                registration_complete=False
            )

            # Connecter l'utilisateur
            login(self.request, user)
            
            logger.info(
                f"Step 1 completed successfully",
                extra={
                    'user_id': user.id,
                    'username': user.username,
                    'ip_address': self.request.META.get('REMOTE_ADDR')
                }
            )

            messages.success(self.request, "Personal information saved successfully. Please complete your company details.")
            return super().form_valid(form)

        except Exception as e:
            logger.error(
                "Error processing registration form step 1",
                exc_info=True,
                extra={
                    'form_data': {
                        k: v for k, v in form.cleaned_data.items() 
                        if k not in ['password1', 'password2']
                    },
                    'ip_address': self.request.META.get('REMOTE_ADDR')
                }
            )
            messages.error(self.request, "An error occurred during registration. Please try again.")
            return self.form_invalid(form)


@method_decorator(never_cache, name='dispatch')
class ClientRegistrationStep2View(FormView):
    template_name = 'client/auth/step2.html'
    form_class = ClientRegistrationForm2
    success_url = reverse_lazy('dbdint:client_dashboard')

    def get(self, request, *args, **kwargs):
        # Si l'utilisateur n'est pas authentifié, rediriger vers l'étape 1
        if not request.user.is_authenticated:
            messages.error(request, "Please complete step 1 first.")
            return redirect('dbdint:client_register')
            
        # Si l'utilisateur a déjà complété son inscription
        if request.user.registration_complete:
            return redirect('dbdint:client_dashboard')
        
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_data'] = {
                'username': self.request.user.username,
                'email': self.request.user.email,
                'first_name': self.request.user.first_name,
                'last_name': self.request.user.last_name,
                'phone': self.request.user.phone
            }
        return context

    def form_valid(self, form):
        try:
            logger.info("Processing valid registration form step 2")
            
            if not self.request.user.is_authenticated:
                messages.error(self.request, "Session expired. Please start over.")
                return redirect('dbdint:client_register')

            # Créer le profil client avec l'utilisateur existant
            client_profile = form.save(commit=False)
            client_profile.user = self.request.user
            client_profile.save()

            # Marquer l'inscription comme complète
            self.request.user.registration_complete = True
            self.request.user.save()
            
            logger.info(
                "Registration completed successfully",
                extra={
                    'user_id': self.request.user.id,
                    'username': self.request.user.username,
                    'ip_address': self.request.META.get('REMOTE_ADDR')
                }
            )

            messages.success(self.request, "Registration completed successfully! Welcome to DBD I&T.")
            return super().form_valid(form)

        except Exception as e:
            logger.error(
                "Error processing registration form step 2",
                exc_info=True,
                extra={
                    'form_data': form.cleaned_data,
                    'ip_address': self.request.META.get('REMOTE_ADDR')
                }
            )
            raise

    def form_invalid(self, form):
        logger.warning(
            "Invalid registration form step 2 submission",
            extra={
                'errors': form.errors,
                'ip_address': self.request.META.get('REMOTE_ADDR')
            }
        )
        return super().form_invalid(form)
    
    
    
class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
    model = NotificationPreference
    form_class = NotificationPreferencesForm
    template_name = 'client/setnotifications.html'
    success_url = reverse_lazy('dbdint:client_dashboard')

    def get_object(self, queryset=None):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

    def form_valid(self, form):
        messages.success(self.request, 'Your notification preferences have been updated!')
        return super().form_valid(form)

class RegistrationSuccessView(TemplateView):
    template_name = 'client/auth/success.html'
    
    



class ClientDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'client/home.html'
    login_url = 'dbdint:login'
    permission_denied_message = "Access denied. This area is for clients only."
    
    def test_func(self):
        user = self.request.user
        
        # Log plus détaillé
        logger.debug(
            "Testing client dashboard access",
            extra={
                'user_id': user.id,
                'role': getattr(user, 'role', 'NO_ROLE'),
                'has_client_profile': hasattr(user, 'client_profile'),
                'registration_complete': user.registration_complete
            }
        )
        
        if not user.role:
            logger.error(f"User {user.id} has no role assigned")
            return False

        return (user.role == User.Roles.CLIENT and 
                hasattr(user, 'client_profile') and 
                user.registration_complete)

    def handle_no_permission(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return redirect(self.login_url)
        
        # Si l'utilisateur n'a pas de rôle
        if not user.role:
            messages.error(self.request, "Your account setup is incomplete. Please contact support.")
            return redirect('dbdint:home')
            
        # Si l'inscription n'est pas complète et que c'est un client
        if user.role == User.Roles.CLIENT and not user.registration_complete:
            if 'registration_step1' in self.request.session:
                return redirect('dbdint:client_register_step2')
            else:
                return redirect('dbdint:client_register')
                
        # Pour les autres rôles
        if user.role == User.Roles.INTERPRETER:
            messages.warning(self.request, "This area is for clients only. Redirecting to interpreter dashboard.")
            return redirect('dbdint:interpreter_dashboard')
        elif user.role == User.Roles.ADMIN:
            return redirect('dbdint:admin_dashboard')
            
        messages.error(self.request, "Access denied. Please complete your registration or contact support.")
        return redirect('dbdint:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            client = self.request.user.client_profile
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
            
            # Données récentes
            context.update({
                'recent_quotes': QuoteRequest.objects.filter(
                    client=client
                ).select_related(
                    'service_type',
                    'source_language',
                    'target_language'
                ).order_by('-created_at')[:5],
                
                'upcoming_assignments': Assignment.objects.filter(
                    client=client,
                    status__in=['CONFIRMED', 'IN_PROGRESS'],
                    start_time__gte=timezone.now()
                ).select_related(
                    'interpreter',
                    'service_type',
                    'source_language',
                    'target_language'
                ).order_by('start_time')[:5],
                
                'recent_payments': Payment.objects.filter(
                    assignment__client=client
                ).select_related(
                    'assignment',
                    'assignment__service_type',
                    'assignment__interpreter'
                ).order_by('-payment_date')[:5],
                
                'unread_notifications': Notification.objects.filter(
                    recipient=self.request.user,
                    read=False
                ).order_by('-created_at')[:5],
                
                'client_profile': client
            })

        except Exception as e:
            logger.error(
                "Error loading client dashboard data",
                exc_info=True,
                extra={
                    'user_id': self.request.user.id,
                    'error': str(e)
                }
            )
            messages.error(
                self.request,
                "There was a problem loading your dashboard data. Please refresh the page or contact support if the problem persists."
            )
            context.update({
                'error_loading_data': True,
                'stats': {
                    'pending_quotes': 0,
                    'active_assignments': 0,
                    'completed_assignments': 0,
                    'total_spent': 0
                }
            })
        
        return context

    def dispatch(self, request, *args, **kwargs):
        if not User.is_authenticated:
            return self.handle_no_permission()
            
        response = super().dispatch(request, *args, **kwargs)
        
        if response.status_code == 200:
            logger.info(
                f"Client dashboard accessed successfully",
                extra={
                    'user_id': request.user.id,
                    'ip_address': request.META.get('REMOTE_ADDR')
                }
            )
            
        return response
class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            # Get notification ID from request data
            notification_id = request.POST.get('notification_id')
            
            if not notification_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Notification ID is required'
                }, status=400)

            # Get notification and verify ownership
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user,
            )
            
            # Mark as read
            notification.read = True
            notification.read_at = timezone.now()
            notification.save()

            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read',
                'notification_id': notification_id
            })

        except Notification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Notification not found'
            }, status=404)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred'
            }, status=500)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'success': False,
            'message': 'Method not allowed'
        }, status=405)

class ClearAllNotificationsView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            # Get all unread notifications for the user
            notifications = Notification.objects.filter(
                recipient=request.user,
                read=False
            )
            
            # Update all notifications
            count = notifications.count()
            notifications.update(
                read=True,
                read_at=timezone.now()
            )

            return JsonResponse({
                'success': True,
                'message': f'{count} notifications marked as read',
                'count': count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'An error occurred'
            }, status=500)

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'success': False,
            'message': 'Method not allowed'
        }, status=405)




class ClientRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is a client"""
    def test_func(self):
        return self.request.user.role == 'CLIENT'
class QuoteRequestListView(LoginRequiredMixin, ClientRequiredMixin, ListView):
    """
    Display all quote requests for the client with filtering and pagination
    """
    model = QuoteRequest
    template_name = 'client/quote_list.html'
    context_object_name = 'quotes'
    paginate_by = 10

    def get_queryset(self):
        queryset = QuoteRequest.objects.filter(
            client=self.request.user.client_profile
        ).order_by('-created_at')

        # Apply filters from form
        filter_form = QuoteFilterForm(self.request.GET)
        if filter_form.is_valid():
            # Status filter
            status = filter_form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)

            # Date range filter
            date_from = filter_form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(requested_date__gte=date_from)

            date_to = filter_form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(requested_date__lte=date_to)

            # Service type filter
            service_type = filter_form.cleaned_data.get('service_type')
            if service_type:
                queryset = queryset.filter(service_type=service_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add filter form
        context['filter_form'] = QuoteFilterForm(self.request.GET)
        
        # Add choices for dropdowns
        context['status_choices'] = QuoteRequest.Status.choices
        # Pour le service_type, on doit faire une requête car c'est un modèle
        context['service_types'] = ServiceType.objects.filter(active=True).values_list('id', 'name')
        
        # Add statistics
        base_queryset = self.get_queryset()
        context['stats'] = {
            'pending_count': base_queryset.filter(status=QuoteRequest.Status.PENDING).count(),
            'processing_count': base_queryset.filter(status=QuoteRequest.Status.PROCESSING).count(),
            'quoted_count': base_queryset.filter(status=QuoteRequest.Status.QUOTED).count(),
            'accepted_count': base_queryset.filter(status=QuoteRequest.Status.ACCEPTED).count()
        }

        # Add current filters to context for pagination
        context['current_filters'] = self.request.GET.dict()
        if 'page' in context['current_filters']:
            del context['current_filters']['page']
            
        return context

class QuoteRequestCreateView(LoginRequiredMixin, ClientRequiredMixin, CreateView):
    """
    Create a new quote request
    """
    model = QuoteRequest
    form_class = QuoteRequestForm
    template_name = 'client/quote_create.html'
    success_url = reverse_lazy('dbdint:client_quote_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.client = self.request.user.client_profile
        form.instance.status = QuoteRequest.Status.PENDING
        response = super().form_valid(form)
        
        messages.success(
            self.request,
            'Your quote request has been successfully submitted. Our team will review it shortly.'
        )
        return response

class QuoteRequestDetailView(LoginRequiredMixin, ClientRequiredMixin, DetailView):
    """
    Display detailed information about a quote request and its timeline
    """
    model = QuoteRequest
    template_name = 'client/quote_detail.html'
    context_object_name = 'quote_request'

    def get_queryset(self):
        return QuoteRequest.objects.filter(
            client=self.request.user.client_profile
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote_request = self.get_object()
        
        # Get related quote if exists
        try:
            context['quote'] = quote_request.quote
        except Quote.DoesNotExist:
            context['quote'] = None

        # Get related assignment if exists
        if context['quote'] and context['quote'].status == 'ACCEPTED':
            try:
                context['assignment'] = context['quote'].assignment
            except Assignment.DoesNotExist:
                context['assignment'] = None

        # Create timeline events
        timeline_events = [
            {
                'date': quote_request.created_at,
                'status': 'CREATED',
                'description': 'Quote request submitted'
            }
        ]
        
        # Add quote events if exists
        if context['quote']:
            timeline_events.append({
                'date': context['quote'].created_at,
                'status': 'QUOTED',
                'description': 'Quote generated and sent'
            })

        # Add assignment events if exists
        if context.get('assignment'):
            timeline_events.append({
                'date': context['assignment'].created_at,
                'status': 'ASSIGNED',
                'description': 'Interpreter assigned'
            })
            if context['assignment'].status == 'COMPLETED':
                timeline_events.append({
                    'date': context['assignment'].completed_at,
                    'status': 'COMPLETED',
                    'description': 'Service completed'
                })

        context['timeline_events'] = sorted(
            timeline_events,
            key=lambda x: x['date'],
            reverse=True
        )

        return context

class QuoteAcceptView(LoginRequiredMixin, ClientRequiredMixin, View):
    """
    Handle quote acceptance
    """
    def post(self, request, *args, **kwargs):
        quote = get_object_or_404(
            Quote,
            quote_request__client=request.user.client_profile,
            pk=kwargs['pk'],
            status='SENT'
        )

        try:
            quote.status = Quote.Status.ACCEPTED
            quote.save()
            
            messages.success(
                request,
                'Quote accepted successfully. Our team will assign an interpreter shortly.'
            )
            return redirect('dbdint:client_quote_detail', pk=quote.quote_request.pk)

        except Exception as e:
            messages.error(request, 'An error occurred while accepting the quote.')
            return redirect('dbdint:quote_detail', pk=quote.quote_request.pk)

class QuoteRejectView(LoginRequiredMixin, ClientRequiredMixin, View):
    """
    Handle quote rejection
    """
    def post(self, request, *args, **kwargs):
        quote = get_object_or_404(
            Quote,
            quote_request__client=request.user.client_profile,
            pk=kwargs['pk'],
            status='SENT'
        )

        try:
            quote.status = Quote.Status.REJECTED
            quote.save()
            
            messages.success(request, 'Quote rejected successfully.')
            return redirect('dbdint:client_quote_detail', pk=quote.quote_request.pk)

        except Exception as e:
            messages.error(request, 'An error occurred while rejecting the quote.')
            return redirect('dbdint:quote_detail', pk=quote.quote_request.pk)

class AssignmentDetailClientView(LoginRequiredMixin, ClientRequiredMixin, DetailView):
    """
    Display assignment details for the client
    """
    model = Assignment
    template_name = 'client/assignment_detail.html'
    context_object_name = 'assignment'

    def get_queryset(self):
        return Assignment.objects.filter(
            client=self.request.user.client_profile
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()

        # Add feedback form if assignment is completed and no feedback exists
        if (assignment.status == 'COMPLETED' and 
            not hasattr(assignment, 'assignmentfeedback')):
            context['feedback_form'] = AssignmentFeedbackForm()

        return context

    def post(self, request, *args, **kwargs):
        """Handle feedback submission"""
        assignment = self.get_object()
        
        if assignment.status != 'COMPLETED':
            messages.error(request, 'Feedback can only be submitted for completed assignments.')
            return redirect('dbdint:client_assignment_detail', pk=assignment.pk)

        if hasattr(assignment, 'assignmentfeedback'):
            messages.error(request, 'Feedback has already been submitted for this assignment.')
            return redirect('dbdint:client_assignment_detail', pk=assignment.pk)

        form = AssignmentFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.assignment = assignment
            feedback.created_by = request.user
            feedback.save()
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('dbdint:client_assignment_detail', pk=assignment.pk)

        context = self.get_context_data(object=assignment)
        context['feedback_form'] = form
        return self.render_to_response(context)




class ProfileView(LoginRequiredMixin, TemplateView):
    """Main profile view that combines user and client profile forms"""
    template_name = 'client/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserProfileForm(instance=self.request.user)
        context['client_form'] = ClientProfileForm(instance=self.request.user.client_profile)
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserProfileForm(request.POST, instance=request.user)
        client_form = ClientProfileForm(request.POST, instance=request.user.client_profile)

        if user_form.is_valid() and client_form.is_valid():
            user_form.save()
            client_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('dbdint:client_profile_edit')
        
        return self.render_to_response(
            self.get_context_data(
                user_form=user_form,
                client_form=client_form
            )
        )
        
        
class ClientProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientProfileUpdateForm
    template_name = 'accounts/profile/update.html'
    success_url = reverse_lazy('dbdint:client_dashboard')

    def get_object(self, queryset=None):
        return self.request.user.client_profile

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)


class ProfilePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """View for changing password"""
    form_class = CustomPasswordChangeForm
    template_name = 'client/change_password.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully.')
        return super().form_valid(form)


#####INTERPRETERDASHBOARD##################################

import logging

logger = logging.getLogger(__name__)

@method_decorator(never_cache, name='dispatch')
class InterpreterRegistrationStep1View(FormView):
   template_name = 'trad/auth/step1.html'
   form_class = InterpreterRegistrationForm1
   success_url = reverse_lazy('dbdint:interpreter_registration_step2')

   def dispatch(self, request, *args, **kwargs):
       logger.info(f"Dispatch called for InterpreterRegistrationStep1View - User authenticated: {request.user.is_authenticated}")
       
       if request.user.is_authenticated:
           logger.info(f"Authenticated user {request.user.email} attempting to access registration. Redirecting to dashboard.")
           return redirect('interpreter_dashboard')
       return super().dispatch(request, *args, **kwargs)

   def form_valid(self, form):
       logger.info("Form validation successful for InterpreterRegistrationStep1View")
       
       try:
           session_data = {
               'username': form.cleaned_data['username'],
               'email': form.cleaned_data['email'],
               'password': form.cleaned_data['password1'],
               'first_name': form.cleaned_data['first_name'],
               'last_name': form.cleaned_data['last_name'],
               'phone': form.cleaned_data['phone']
           }
           self.request.session['dbdint:interpreter_registration_step1'] = session_data
           logger.info(f"Session data saved successfully for username: {session_data['username']}, email: {session_data['email']}")
           
       except Exception as e:
           logger.error(f"Error saving session data: {str(e)}")
           messages.error(self.request, 'An error occurred while saving your information.')
           return self.form_invalid(form)
       
       logger.info(f"Redirecting to step 2 for username: {session_data['username']}")
       return super().form_valid(form)

   def form_invalid(self, form):
       logger.warning("Form validation failed for InterpreterRegistrationStep1View")
       logger.debug(f"Form errors: {form.errors}")
       
       messages.error(self.request, 'Please correct the errors below.')
       return super().form_invalid(form)

   def get(self, request, *args, **kwargs):
       logger.info("GET request received for InterpreterRegistrationStep1View")
       return super().get(request, *args, **kwargs)

   def post(self, request, *args, **kwargs):
       logger.info("POST request received for InterpreterRegistrationStep1View")
       logger.debug(f"POST data: {request.POST}")
       return super().post(request, *args, **kwargs)

@method_decorator(never_cache, name='dispatch')
class InterpreterRegistrationStep2View(FormView):
   template_name = 'trad/auth/step2.html'
   form_class = InterpreterRegistrationForm2
   success_url = reverse_lazy('dbdint:interpreter_registration_step3')

   def get_context_data(self, **kwargs):
       logger.info("Getting context data for InterpreterRegistrationStep2View")
       context = super().get_context_data(**kwargs)
       
       try:
           context['languages'] = Language.objects.filter(is_active=True)
           logger.debug(f"Found {context['languages'].count()} active languages")
           
           step2_data = self.request.session.get('dbdint:interpreter_registration_step2')
           if step2_data and 'languages' in step2_data:
               context['selected_languages'] = step2_data['languages']
               logger.debug(f"Retrieved previously selected languages: {step2_data['languages']}")
       except Exception as e:
           logger.error(f"Error getting context data: {str(e)}")
           
       return context

   def dispatch(self, request, *args, **kwargs):
       logger.info("Dispatch called for InterpreterRegistrationStep2View")
       
       if not request.session.get('dbdint:interpreter_registration_step1'):
           logger.warning("Step 1 data not found in session. Redirecting to step 1.")
           messages.error(request, 'Please complete step 1 first.')
           return redirect('dbdint:interpreter_registration_step1')
           
       logger.debug("Step 1 data found in session. Proceeding with step 2.")
       return super().dispatch(request, *args, **kwargs)

   def form_valid(self, form):
       logger.info("Form validation successful for InterpreterRegistrationStep2View")
       
       try:
           selected_languages = [str(lang.id) for lang in form.cleaned_data['languages']]
           logger.debug(f"Selected languages: {selected_languages}")
           
           self.request.session['dbdint:interpreter_registration_step2'] = {
               'languages': selected_languages
           }
           logger.info("Session data saved successfully")
           
       except Exception as e:
           logger.error(f"Error saving session data: {str(e)}")
           messages.error(self.request, 'An error occurred while saving your information.')
           return self.form_invalid(form)
           
       return super().form_valid(form)

   def form_invalid(self, form):
       logger.warning("Form validation failed for InterpreterRegistrationStep2View")
       logger.debug(f"Form errors: {form.errors}")
       messages.error(self.request, 'Please correct the errors below.')
       return super().form_invalid(form)

   def get_initial(self):
       logger.info("Getting initial data for InterpreterRegistrationStep2View")
       initial = super().get_initial()
       
       try:
           step2_data = self.request.session.get('dbdint:interpreter_registration_step2')
           if step2_data and 'languages' in step2_data:
               initial['languages'] = [int(lang_id) for lang_id in step2_data['languages']]
               logger.debug(f"Retrieved initial languages data: {initial['languages']}")
       except Exception as e:
           logger.error(f"Error getting initial data: {str(e)}")
           
       return initial

   def get(self, request, *args, **kwargs):
       logger.info("GET request received for InterpreterRegistrationStep2View")
       return super().get(request, *args, **kwargs)

   def post(self, request, *args, **kwargs):
       logger.info("POST request received for InterpreterRegistrationStep2View")
       logger.debug(f"POST data: {request.POST}")
       return super().post(request, *args, **kwargs)







@method_decorator(never_cache, name='dispatch')
class InterpreterRegistrationStep3View(FormView):
   template_name = 'trad/auth/step3.html'
   form_class = InterpreterRegistrationForm3 
   success_url = reverse_lazy('dbdint:interpreter_dashboard')

   def get_context_data(self, **kwargs):
       logger.info("Getting context data for InterpreterRegistrationStep3View")
       context = super().get_context_data(**kwargs)
       context['current_step'] = 3
       context['states'] = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
        }
       logger.debug(f"Context data prepared with {len(context['states'])} states")
       return context

   def dispatch(self, request, *args, **kwargs):
       logger.info("Dispatch called for InterpreterRegistrationStep3View")
       step1_exists = 'dbdint:interpreter_registration_step1' in request.session
       step2_exists = 'dbdint:interpreter_registration_step2' in request.session
       
       if not all([step1_exists, step2_exists]):
           logger.warning("Previous steps data missing")
           messages.error(request, 'Please complete previous steps first.')
           return redirect('dbdint:interpreter_registration_step1')
       return super().dispatch(request, *args, **kwargs)

   def form_valid(self, form):
       logger.info("Form validation successful")
       try:
           step1_data = self.request.session['dbdint:interpreter_registration_step1']
           step2_data = self.request.session['dbdint:interpreter_registration_step2']
           
           user = User.objects.create_user(
               username=step1_data['username'],
               email=step1_data['email'],
               password=step1_data['password'],
               first_name=step1_data['first_name'],
               last_name=step1_data['last_name'],
               phone=step1_data['phone'],
               role='INTERPRETER'
           )
           logger.info(f"User created: {user.email}")

           interpreter = form.save(commit=False)
           interpreter.user = user
           interpreter.save()
           
           for language_id in step2_data['languages']:
               interpreter.languages.add(language_id)
           
           del self.request.session['dbdint:interpreter_registration_step1']
           del self.request.session['dbdint:interpreter_registration_step2']

           login(self.request, user)
           messages.success(self.request, 'Your interpreter account has been created successfully! Our team will review your application.')
           return super().form_valid(form)

       except Exception as e:
           logger.error(f"Registration error: {str(e)}", exc_info=True)
           messages.error(self.request, 'An error occurred while creating your account.')
           return redirect('dbdint:interpreter_registration_step1')

   def form_invalid(self, form):
       logger.warning(f"Form validation failed: {form.errors}")
       messages.error(self.request, 'Please correct the errors below.')
       return super().form_invalid(form)


class InterpreterDashboardView(LoginRequiredMixin, UserPassesTestMixin,TemplateView):
    template_name = 'trad/home.html'
    
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
    
    
    
# views.py


class InterpreterSettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'trad/settings.html'
    
    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get_notification_preferences(self):
        try:
            return NotificationPreference.objects.get(user=self.request.user)
        except NotificationPreference.DoesNotExist:
            return NotificationPreference.objects.create(
                user=self.request.user,
                email_quote_updates=True,
                email_assignment_updates=True,
                email_payment_updates=True,
                sms_enabled=False,
                quote_notifications=True,
                assignment_notifications=True,
                payment_notifications=True,
                system_notifications=True,
                notification_frequency='immediate',
                preferred_language=None
            )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # S'assure que les préférences de notification existent
        notification_preference = self.get_notification_preferences()
        
        if self.request.POST:
            context['profile_form'] = InterpreterProfileForm(
                self.request.POST, 
                self.request.FILES,
                user=user,
                instance=user.interpreter_profile
            )
            context['notification_form'] = NotificationPreferenceForm(
                self.request.POST,
                instance=notification_preference
            )
            context['password_form'] = CustomPasswordtradChangeForm(user, self.request.POST)
        else:
            context['profile_form'] = InterpreterProfileForm(
                user=user,
                instance=user.interpreter_profile
            )
            context['notification_form'] = NotificationPreferenceForm(
                instance=notification_preference
            )
            context['password_form'] = CustomPasswordtradChangeForm(user)
        
        return context
    
    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        action = request.POST.get('action')
        
        if action == 'update_profile':
            profile_form = context['profile_form']
            if profile_form.is_valid():
                profile = profile_form.save(commit=False)
                user = request.user
                
                # Mise à jour des informations utilisateur
                user.first_name = profile_form.cleaned_data['first_name']
                user.last_name = profile_form.cleaned_data['last_name']
                user.email = profile_form.cleaned_data['email']
                user.phone_number = profile_form.cleaned_data['phone_number']
                user.save()
                
                # Mise à jour des informations bancaires
                profile.bank_name = profile_form.cleaned_data['bank_name']
                profile.account_holder_name = profile_form.cleaned_data['account_holder']
                profile.account_number = profile_form.cleaned_data['account_number']
                profile.routing_number = profile_form.cleaned_data['routing_number']
                
                profile.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('dbdint:interpreter_settings')
                
        elif action == 'update_notifications':
            notification_form = context['notification_form']
            if notification_form.is_valid():
                notification_form.save()
                messages.success(request, 'Notification preferences updated successfully!')
                return redirect('dbdint:interpreter_settings')
                
        elif action == 'change_password':
            password_form = context['password_form']
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Password changed successfully!')
                return redirect('dbdint:interpreter_settings')
        
        return self.render_to_response(context)
    
# views.py


class NotificationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Notification
    template_name = 'trad/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Grouper les notifications par catégorie
        context['unread_notifications'] = self.get_queryset().filter(read=False)
        context['quote_notifications'] = self.get_queryset().filter(
            Q(type='QUOTE_REQUEST') | Q(type='QUOTE_READY')
        )
        context['assignment_notifications'] = self.get_queryset().filter(
            Q(type='ASSIGNMENT_OFFER') | Q(type='ASSIGNMENT_REMINDER')
        )
        context['payment_notifications'] = self.get_queryset().filter(
            type='PAYMENT_RECEIVED'
        )
        context['system_notifications'] = self.get_queryset().filter(
            type='SYSTEM'
        )
        
        return context

@require_POST
def mark_notification_as_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@require_POST
def mark_all_notifications_as_read(request):
    Notification.objects.filter(
        recipient=request.user,
        read=False
    ).update(read=True)
    return JsonResponse({'status': 'success'})


# views.py

class InterpreterScheduleView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'trad/schedule.html'

    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interpreter = self.request.user.interpreter_profile

        # Récupérer la date actuelle
        now = timezone.now()
        
        # Prochaines missions (limitées à 5)
        context['upcoming_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status__in=['CONFIRMED', 'ASSIGNED'],
            start_time__gte=now
        ).order_by('start_time')[:5]

        # Missions en cours
        context['current_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='IN_PROGRESS'
        )

        # Statistiques de la semaine
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        weekly_assignments = Assignment.objects.filter(
            interpreter=interpreter,
            start_time__range=(week_start, week_end),
            status__in=['CONFIRMED', 'IN_PROGRESS', 'COMPLETED']
        )

        context['weekly_stats'] = {
            'total_assignments': weekly_assignments.count(),
            'total_hours': sum(
                (a.end_time - a.start_time).total_seconds() / 3600 
                for a in weekly_assignments
            ),
            'earnings': sum(a.total_interpreter_payment or 0 for a in weekly_assignments)
        }

        return context

def get_calendar_assignments(request):
    """Vue API pour récupérer les missions pour le calendrier"""
    if not request.user.is_authenticated or request.user.role != 'INTERPRETER':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    start = request.GET.get('start')
    end = request.GET.get('end')
    interpreter = request.user.interpreter_profile

    assignments = Assignment.objects.filter(
        interpreter=interpreter,
        start_time__range=[start, end]
    ).select_related('client', 'service_type')

    events = []
    status_colors = {
        'PENDING': '#FFA500',    # Orange
        'ASSIGNED': '#4299e1',   # Bleu clair
        'CONFIRMED': '#48bb78',  # Vert
        'IN_PROGRESS': '#805ad5', # Violet
        'COMPLETED': '#718096',  # Gris
        'CANCELLED': '#f56565',  # Rouge
        'NO_SHOW': '#ed8936',    # Orange foncé
    }

    for assignment in assignments:
        events.append({
            'id': assignment.id,
            'title': f"{assignment.client.full_name} - {assignment.service_type.name}",
            'start': assignment.start_time.isoformat(),
            'end': assignment.end_time.isoformat(),
            'backgroundColor': status_colors[assignment.status],
            'borderColor': status_colors[assignment.status],
            'extendedProps': {
                'status': assignment.status,
                'location': assignment.location,
                'city': assignment.city,
                'languages': f"{assignment.source_language.name} → {assignment.target_language.name}",
                'rate': float(assignment.interpreter_rate),
                'hours': (assignment.end_time - assignment.start_time).total_seconds() / 3600,
                'total_payment': float(assignment.total_interpreter_payment or 0),
                'special_requirements': assignment.special_requirements or 'None'
            }
        })

    return JsonResponse(events, safe=False)





class AssignmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'trad/assignment.html'
    context_object_name = 'assignments'

    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get_queryset(self):
        return Assignment.objects.filter(
            interpreter=self.request.user.interpreter_profile
        ).order_by('start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interpreter = self.request.user.interpreter_profile
        now = timezone.now()
        
        # Assignments en attente de confirmation (PENDING)
        context['pending_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='PENDING'
        ).order_by('start_time')
        
        # Assignments confirmés à venir
        context['upcoming_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='CONFIRMED',
            start_time__gt=now
        ).order_by('start_time')
        
        # Assignments en cours
        context['in_progress_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='IN_PROGRESS'
        ).order_by('start_time')
        
        # Assignments terminés (derniers 30 jours)
        thirty_days_ago = now - timedelta(days=30)
        context['completed_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='COMPLETED',
            completed_at__gte=thirty_days_ago
        ).order_by('-completed_at')
        
        return context






class AssignmentDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get(self, request, pk):
        assignment = get_object_or_404(Assignment, pk=pk)
        
        if assignment.interpreter != request.user.interpreter_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        data = {
            'id': assignment.id,
            'start_time': assignment.start_time.isoformat(),
            'end_time': assignment.end_time.isoformat(),
            'location': assignment.location,
            'city': assignment.city,
            'state': assignment.state,
            'zip_code': assignment.zip_code,
            'service_type': assignment.service_type.name,
            'source_language': assignment.source_language.name,
            'target_language': assignment.target_language.name,
            'interpreter_rate': str(assignment.interpreter_rate),
            'minimum_hours': assignment.minimum_hours,
            'status': assignment.status,
            'special_requirements': assignment.special_requirements or '',
            'notes': assignment.notes or '',
            'can_start': assignment.can_be_started(),
            'can_complete': assignment.can_be_completed(),
            'can_cancel': assignment.can_be_cancelled()
        }
        
        return JsonResponse(data)

@require_POST
def accept_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if assignment.interpreter != request.user.interpreter_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if not assignment.can_be_confirmed():
        return JsonResponse({'error': 'Invalid status'}, status=400)

    # Vérifier les conflits d'horaire
    conflicting_assignments = Assignment.objects.filter(
        interpreter=request.user.interpreter_profile,
        status__in=['CONFIRMED', 'IN_PROGRESS'],
        start_time__lt=assignment.end_time,
        end_time__gt=assignment.start_time
    ).exists()

    if conflicting_assignments:
        return JsonResponse({
            'error': 'Schedule conflict',
            'message': 'You already have an assignment during this time period'
        }, status=400)

    if assignment.confirm():
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Could not confirm assignment'}, status=400)

@require_POST
def reject_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if assignment.interpreter != request.user.interpreter_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if not assignment.can_be_cancelled():
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    old_interpreter = assignment.cancel()
    if old_interpreter:
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Could not reject assignment'}, status=400)

@require_POST
def start_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if assignment.interpreter != request.user.interpreter_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if not assignment.can_be_started():
        return JsonResponse({'error': 'Invalid status'}, status=400)

    # Vérifier la fenêtre de temps (15 minutes avant)
    if timezone.now() + timedelta(minutes=15) < assignment.start_time:
        return JsonResponse({
            'error': 'Too early',
            'message': 'You can only start the assignment 15 minutes before the scheduled time'
        }, status=400)

    if assignment.start():
        return JsonResponse({'status': 'success'})
    return JsonResponse({'error': 'Could not start assignment'}, status=400)

@require_POST
def complete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if assignment.interpreter != request.user.interpreter_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if not assignment.can_be_completed():
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    if assignment.complete():
        return JsonResponse({
            'status': 'success',
            'payment': str(assignment.total_interpreter_payment)
        })
    return JsonResponse({'error': 'Could not complete assignment'}, status=400)

def get_assignment_counts(request):
    if not request.user.is_authenticated or request.user.role != 'INTERPRETER':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    interpreter = request.user.interpreter_profile
    
    counts = {
        'pending': Assignment.objects.filter(interpreter=interpreter, status='PENDING').count(),
        'upcoming': Assignment.objects.filter(interpreter=interpreter, status='CONFIRMED').count(),
        'in_progress': Assignment.objects.filter(interpreter=interpreter, status='IN_PROGRESS').count(),
        'completed': Assignment.objects.filter(interpreter=interpreter, status='COMPLETED').count()
    }
    
    return JsonResponse(counts)

@require_POST
def mark_assignments_as_read(request):
    interpreter = request.user.interpreter_profile
    AssignmentNotification.objects.filter(
        interpreter=interpreter,
        is_read=False
    ).update(is_read=True)
    return JsonResponse({'status': 'success'})

def get_unread_assignments_count(request):
    if not request.user.is_authenticated or request.user.role != 'INTERPRETER':
        return JsonResponse({'count': 0})
        
    count = AssignmentNotification.get_unread_count(
        request.user.interpreter_profile
    )
    return JsonResponse({'count': count})
# views.py


class TranslatorEarningsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'trad/earnings.html'

    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interpreter = self.request.user.interpreter_profile
        now = timezone.now()

        # Statistiques générales
        all_payments = Payment.objects.filter(
            assignment__interpreter=interpreter,
            payment_type='INTERPRETER_PAYMENT'
        )

        # Statistiques du mois en cours
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_payments = all_payments.filter(payment_date__gte=current_month_start)

        context['current_month'] = {
            'earnings': current_month_payments.filter(status='COMPLETED').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00'),
            'pending': current_month_payments.filter(status='PENDING').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00'),
            'assignments': current_month_payments.count(),
        }

        # Statistiques des 12 derniers mois
        twelve_months_ago = now - timedelta(days=365)
        monthly_earnings = all_payments.filter(
            payment_date__gte=twelve_months_ago,
            status='COMPLETED'
        ).annotate(
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')

        context['monthly_earnings'] = monthly_earnings

        # Statistiques annuelles
        yearly_earnings = all_payments.filter(
            status='COMPLETED'
        ).annotate(
            year=TruncYear('payment_date')
        ).values('year').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-year')

        context['yearly_earnings'] = yearly_earnings

        # Paiements récents
        context['recent_payments'] = all_payments.select_related(
            'assignment'
        ).order_by('-payment_date')[:10]

        # Paiements en attente
        context['pending_payments'] = all_payments.filter(
            status='PENDING'
        ).select_related('assignment').order_by('-payment_date')

        # Statistiques globales
        context['total_stats'] = {
            'lifetime_earnings': all_payments.filter(status='COMPLETED').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00'),
            'total_assignments': all_payments.filter(status='COMPLETED').count(),
            'pending_amount': all_payments.filter(status='PENDING').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00'),
            'average_payment': all_payments.filter(
                status='COMPLETED'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00') / (
                all_payments.filter(status='COMPLETED').count() or 1
            )
        }

        # Liste des années pour le filtre
        context['years'] = yearly_earnings.values_list('year', flat=True)

        return context



@require_GET
def get_earnings_data(request, year=None):
    """Vue API pour obtenir les données des gains pour les graphiques"""
    interpreter = request.user.interpreter_profile
    payments = Payment.objects.filter(
        assignment__interpreter=interpreter,
        payment_type='INTERPRETER_PAYMENT'
    )

    if year:
        payments = payments.filter(payment_date__year=year)

    # Données mensuelles
    monthly_data = payments.filter(
        status='COMPLETED'
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')

    # Formatter les données pour les graphiques
    chart_data = {
        'labels': [],
        'earnings': [],
        'assignments': []
    }

    for data in monthly_data:
        chart_data['labels'].append(data['month'].strftime('%B %Y'))
        chart_data['earnings'].append(float(data['total']))
        chart_data['assignments'].append(data['count'])

    return JsonResponse(chart_data)


######################payroll
def generate_document_id():
    """Generate a unique document ID with format: DBD-YYYYMMDD-XXXX"""
    date_str = timezone.now().strftime('%Y%m%d')
    # Generate 4 random characters (letters and numbers)
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"DBD-{date_str}-{random_chars}"

def create_statement(request):
    if request.method == 'POST':
        statement_form = InterpreterStatementForm(request.POST)
        
        if statement_form.is_valid():
            # Create statement with generated document ID
            statement = statement_form.save(commit=False)
            statement.document_id = generate_document_id()
            statement.save()
            
            # Handle multiple services
            service_data = {}
            for key, value in request.POST.items():
                if key.startswith('service-'):
                    parts = key.split('-')
                    if len(parts) == 3:
                        index = parts[1]
                        field = parts[2]
                        if index not in service_data:
                            service_data[index] = {}
                        service_data[index][field] = value
            
            # Create services
            for service_info in service_data.values():
                service_form = InterpreterServiceForm(service_info)
                if service_form.is_valid():
                    service = service_form.save(commit=False)
                    service.statement = statement
                    service.save()
            
            messages.success(request, 'Statement created successfully!')
            return redirect('dbdint:view_contract', pk=statement.pk)
    else:
        statement_form = InterpreterStatementForm()
        service_form = InterpreterServiceForm()
    
    return render(request, 'docs/create_statement.html', {
        'statement_form': statement_form,
        'service_form': service_form,
    })

def view_contract(request, pk):
    statement = get_object_or_404(InterpreterStatement, pk=pk)
    services = InterpreterService.objects.filter(statement=statement)
    
    # Calculate totals
    total_hours = sum(service.hours or Decimal('0.0') for service in services)
    total_amount = sum(
        (service.hours or Decimal('0.0')) * (service.rate or Decimal('0.0')) 
        for service in services
    )
    
    context = {
        'document_id': statement.document_id,
        'current_date': timezone.now().strftime('%B %d, %Y'),
        'current_year': timezone.now().year,
        'client_name': statement.name,
        'client_address_line1': statement.address_line1,
        'client_address_line2': statement.address_line2,
        'client_phone': statement.phone,
        'client_email': statement.email,
        'services': services,
        'total_hours': total_hours,
        'total_amount': total_amount,
    }
    
    return render(request, 'docs/contract.html', context)






