# views.py

# Django core imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.mail import send_mail
from django.core.paginator import Paginator
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
    Assignment,
    Client,
    ContactMessage,
    Notification,
    NotificationPreference,
    Payment,
    PublicQuoteRequest,
    Quote,
    QuoteRequest,
    User,
)
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

   def dispatch(self, request, *args, **kwargs):
       logger.info(f"Dispatching registration request for IP: {request.META.get('REMOTE_ADDR')}")
       
       if request.user.is_authenticated:
           logger.debug(f"Already authenticated user {request.user.id} redirected to dashboard")
           return redirect('dbdint:client_dashboard')
       
       try:
           return super().dispatch(request, *args, **kwargs)
       except Exception as e:
           logger.error("Error in registration dispatch", exc_info=True)
           raise

   def form_valid(self, form):
       try:
           logger.info("Processing valid registration form step 1")
           
           # Store step 1 data in session
           registration_data = {
               'email': form.cleaned_data['email'],
               'password': '[FILTERED]',  # On ne log pas le mot de passe
               'first_name': form.cleaned_data['first_name'],
               'last_name': form.cleaned_data['last_name'],
               'phone': form.cleaned_data['phone']
           }
           
           logger.debug(
               "Storing registration step 1 data in session",
               extra={
                   'email': form.cleaned_data['email'],
                   'first_name': form.cleaned_data['first_name'],
                   'last_name': form.cleaned_data['last_name']
               }
           )

           self.request.session['registration_step1'] = {
               'email': form.cleaned_data['email'],
               'password': form.cleaned_data['password1'],
               'first_name': form.cleaned_data['first_name'], 
               'last_name': form.cleaned_data['last_name'],
               'phone': form.cleaned_data['phone']
           }

           return super().form_valid(form)

       except Exception as e:
           logger.error(
               "Error processing registration form step 1",
               exc_info=True,
               extra={'form_data': form.cleaned_data}
           )
           raise

   def form_invalid(self, form):
       logger.warning(
           "Invalid registration form submission",
           extra={
               'errors': form.errors,
               'ip_address': self.request.META.get('REMOTE_ADDR')
           }
       )
       return super().form_invalid(form)
   
   

@method_decorator(never_cache, name='dispatch')
class ClientRegistrationStep2View(FormView):
   template_name = 'client/auth/step2.html'
   form_class = ClientRegistrationForm2
   success_url = reverse_lazy('dbdint:client_dashboard')

   def dispatch(self, request, *args, **kwargs):
       logger.info(f"Dispatching registration step 2 for IP: {request.META.get('REMOTE_ADDR')}")

       if not request.session.get('dbdint:registration_step1'):
           logger.warning("Step 1 data missing in session, redirecting to step 1")
           return redirect('dbdint:client_register')
           
       try:
           return super().dispatch(request, *args, **kwargs)
       except Exception as e:
           logger.error("Error in step 2 dispatch", exc_info=True)
           raise

   def form_valid(self, form):
       try:
           logger.info("Processing valid registration form step 2")
           step1_data = self.request.session['dbdint:registration_step1']
           
           logger.debug(
               "Retrieved step 1 data from session",
               extra={
                   'email': step1_data['email'],
                   'first_name': step1_data['first_name']
               }
           )

           # Create user
           user = User.objects.create_user(
               email=step1_data['email'],
               password=step1_data['password'],
               first_name=step1_data['first_name'],
               last_name=step1_data['last_name'],
               phone=step1_data['phone'],
               role='CLIENT'
           )
           
           logger.info(f"Created new user with ID: {user.id}")

           # Create client profile
           try:
               client = form.save(commit=False)
               client.user = user
               client.save()
               logger.info(f"Created client profile for user {user.id}")
           except Exception as e:
               logger.error(f"Failed to create client profile for user {user.id}", exc_info=True)
               # Clean up created user if profile creation fails
               user.delete()
               raise

           # Clean up session
           del self.request.session['dbdint:registration_step1']
           logger.debug("Cleaned up session data")

           # Log the user in
           login(self.request, user)
           logger.info(f"Successfully logged in user {user.id}")
           
           messages.success(self.request, 'Your account has been created successfully!')
           return super().form_valid(form)

       except Exception as e:
           logger.error(
               "Error processing registration step 2",
               exc_info=True,
               extra={'form_data': form.cleaned_data}
           )
           messages.error(self.request, 'An error occurred during registration. Please try again.')
           raise

   def form_invalid(self, form):
       logger.warning(
           "Invalid registration form step 2 submission",
           extra={
               'errors': form.errors,
               'ip_address': self.request.META.get('REMOTE_ADDR')
           }
       )
       messages.error(self.request, 'Please correct the errors below.')
       return super().form_invalid(form)

   def get_context_data(self, **kwargs):
       try:
           context = super().get_context_data(**kwargs)
           step1_data = self.request.session.get('dbdint:registration_step1', {})
           logger.debug(
               "Adding step 1 data to context",
               extra={'email': step1_data.get('email')}
           )
           context['step1_data'] = step1_data
           return context
       except Exception as e:
           logger.error("Error getting context data", exc_info=True)
           raise


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
    
    



class ClientDashboardView(LoginRequiredMixin, UserPassesTestMixin):
    template_name = 'client/home.html'
    
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
        context['filter_form'] = QuoteFilterForm(self.request.GET)
        
        # Add statistics
        context['stats'] = {
            'pending_count': self.get_queryset().filter(status='PENDING').count(),
            'processing_count': self.get_queryset().filter(status='PROCESSING').count(),
            'quoted_count': self.get_queryset().filter(status='QUOTED').count(),
            'accepted_count': self.get_queryset().filter(status='ACCEPTED').count()
        }
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
            return redirect('profile')
        
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

@method_decorator(never_cache, name='dispatch')
class InterpreterRegistrationStep1View(FormView):
    template_name = 'trad/auth/step1.html'
    form_class = InterpreterRegistrationForm1
    success_url = reverse_lazy('dbdint:interpreter_registration_step2')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('interpreter_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session['dbdint:interpreter_registration_step1'] = {
            'email': form.cleaned_data['email'],
            'password': form.cleaned_data['password1'],
            'first_name': form.cleaned_data['first_name'],
            'last_name': form.cleaned_data['last_name'],
            'phone': form.cleaned_data['phone']
        }
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

@method_decorator(never_cache, name='dispatch')
class InterpreterRegistrationStep2View(FormView):
    template_name = 'trad/auth/step2.html'
    form_class = InterpreterRegistrationForm2
    success_url = reverse_lazy('dbdint:interpreter_registration_step3')

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('dbdint:interpreter_registration_step1'):
            messages.error(request, 'Please complete step 1 first.')
            return redirect('dbdint:interpreter_registration_step1')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session['dbdint:interpreter_registration_step2'] = {
            'languages': [str(lang.id) for lang in form.cleaned_data['languages']],
            'certifications': form.cleaned_data['certifications'],
            'specialties': form.cleaned_data['specialties'],
            'hourly_rate': str(form.cleaned_data['hourly_rate'])
        }
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

@method_decorator(never_cache, name='dispatch')
class InterpreterRegistrationStep3View(FormView):
    template_name = 'trad/auth/step3.html'
    form_class = InterpreterRegistrationForm3
    success_url = reverse_lazy('dbdint:interpreter_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not all([
            request.session.get('dbdint:interpreter_registration_step1'),
            request.session.get('dbdint:interpreter_registration_step2')
        ]):
            messages.error(request, 'Please complete previous steps first.')
            return redirect('dbdint:interpreter_registration_step1')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            # Récupérer les données des étapes précédentes
            step1_data = self.request.session['dbdint:interpreter_registration_step1']
            step2_data = self.request.session['dbdint:interpreter_registration_step2']

            # Créer l'utilisateur
            user = User.objects.create_user(
                email=step1_data['email'],
                password=step1_data['password'],
                first_name=step1_data['first_name'],
                last_name=step1_data['last_name'],
                phone=step1_data['phone'],
                role='INTERPRETER'
            )

            # Créer le profil d'interprète
            interpreter = form.save(commit=False)
            interpreter.user = user
            interpreter.certifications = step2_data['certifications']
            interpreter.specialties = step2_data['specialties']
            interpreter.hourly_rate = step2_data['hourly_rate']
            interpreter.save()

            # Ajouter les langues
            for language_id in step2_data['languages']:
                interpreter.languages.add(language_id)

            # Nettoyer la session
            del self.request.session['dbdint:interpreter_registration_step1']
            del self.request.session['dbdint:interpreter_registration_step2']

            # Connecter l'utilisateur
            login(self.request, user)
            messages.success(
                self.request, 
                'Your interpreter account has been created successfully! Our team will review your application.'
            )
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, 'An error occurred while creating your account. Please try again.')
            return redirect('dbdint:interpreter_registration_step1')

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class InterpreterDashboardView(LoginRequiredMixin, UserPassesTestMixin):
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


class InterpreterSettingsView(LoginRequiredMixin, UserPassesTestMixin):
    template_name = 'trad/settings.html'
    
    def test_func(self):
        return self.request.user.role == 'INTERPRETER'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if self.request.POST:
            context['profile_form'] = InterpreterProfileForm(
                self.request.POST, 
                self.request.FILES,
                user=user,
                instance=user.interpreter_profile
            )
            context['notification_form'] = NotificationPreferenceForm(
                self.request.POST,
                instance=user.notification_preferences
            )
            context['password_form'] = CustomPasswordtradChangeForm(user, self.request.POST)
        else:
            context['profile_form'] = InterpreterProfileForm(
                user=user,
                instance=user.interpreter_profile
            )
            context['notification_form'] = NotificationPreferenceForm(
                instance=user.notification_preferences
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
                bank_info = user.interpreter_profile.bank_info
                bank_info.bank_name = profile_form.cleaned_data['bank_name']
                bank_info.account_holder = profile_form.cleaned_data['account_holder']
                bank_info.account_number = profile_form.cleaned_data['account_number']
                bank_info.routing_number = profile_form.cleaned_data['routing_number']
                bank_info.save()
                
                profile.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('interpreter_settings')
                
        elif action == 'update_notifications':
            notification_form = context['notification_form']
            if notification_form.is_valid():
                notification_form.save()
                messages.success(request, 'Notification preferences updated successfully!')
                return redirect('interpreter_settings')
                
        elif action == 'change_password':
            password_form = context['password_form']
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Password changed successfully!')
                return redirect('interpreter_settings')
        
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
    template_name = 'trad/assignments.html'
    context_object_name = 'assignments'

    def test_func(self):
        return self.request.user.role == 'INTERPRETER'

    def get_queryset(self):
        return Assignment.objects.filter(
            interpreter=self.request.user.interpreter_profile
        ).exclude(
            status__in=['CANCELLED', 'NO_SHOW']
        ).order_by('start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interpreter = self.request.user.interpreter_profile
        
        # Missions en attente de confirmation
        context['pending_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='PENDING'
        ).order_by('start_time')
        
        # Missions à venir (confirmées)
        context['upcoming_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='CONFIRMED',
            start_time__gt=timezone.now()
        ).order_by('start_time')
        
        # Missions en cours
        context['in_progress_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='IN_PROGRESS'
        ).order_by('start_time')
        
        # Missions terminées (derniers 30 jours)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        context['completed_assignments'] = Assignment.objects.filter(
            interpreter=interpreter,
            status='COMPLETED',
            completed_at__gte=thirty_days_ago
        ).order_by('-completed_at')
        
        return context

class AssignmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Assignment
    template_name = 'trad/assignment_detail.html'
    context_object_name = 'assignment'

    def test_func(self):
        assignment = self.get_object()
        return self.request.user.interpreter_profile == assignment.interpreter

@require_POST
def accept_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if assignment.interpreter != request.user.interpreter_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if assignment.status != 'PENDING':
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    assignment.status = 'CONFIRMED'
    assignment.save()
    
    # Créer une notification pour le client
    Notification.objects.create(
        recipient=assignment.client.user,
        type='ASSIGNMENT_ACCEPTED',
        title='Interpreter accepted your assignment',
        content=f'Your interpreter has confirmed the assignment for {assignment.start_time.strftime("%B %d, %Y at %I:%M %p")}'
    )
    
    return JsonResponse({'status': 'success'})

@require_POST
def reject_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if assignment.interpreter != request.user.interpreter_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if assignment.status != 'PENDING':
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    assignment.status = 'CANCELLED'
    assignment.save()
    
    # Notification pour le client
    Notification.objects.create(
        recipient=assignment.client.user,
        type='ASSIGNMENT_REJECTED',
        title='Interpreter declined your assignment',
        content=f'Unfortunately, the interpreter is not available for your assignment on {assignment.start_time.strftime("%B %d, %Y")}'
    )
    
    return JsonResponse({'status': 'success'})

@require_POST
def complete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    
    if assignment.interpreter != request.user.interpreter_profile:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if assignment.status != 'IN_PROGRESS':
        return JsonResponse({'error': 'Invalid status'}, status=400)
        
    assignment.status = 'COMPLETED'
    assignment.completed_at = timezone.now()
    assignment.save()
    
    # Calculer le paiement de l'interprète
    duration = assignment.end_time - assignment.start_time
    hours = duration.total_seconds() / 3600
    total_payment = max(
        assignment.minimum_hours * float(assignment.interpreter_rate),
        hours * float(assignment.interpreter_rate)
    )
    assignment.total_interpreter_payment = total_payment
    assignment.save()
    
    # Créer un paiement
    Payment.objects.create(
        assignment=assignment,
        amount=total_payment,
        payment_type='INTERPRETER_PAYMENT',
        status='PENDING'
    )
    
    return JsonResponse({'status': 'success'})


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