# urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'dbdint'

urlpatterns = [
    # Public Pages
    path('home', views.PublicQuoteRequestView.as_view(), name='home'),
    path('request-quote/success/', views.QuoteRequestSuccessView.as_view(), name='quote_request_success'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/success/', views.ContactSuccessView.as_view(), name='contact_success'),

    # Authentication
    path('', views.CustomLoginView.as_view(), name='login'),
    path('register/choose/', 
     views.ChooseRegistrationTypeView.as_view(), 
     name='choose_registration'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dbdint:login'), name='logout'),
    
    # Client Registration
    path('client/register/', views.ClientRegistrationView.as_view(), name='client_register'),
    path('client/register/step2/', views.ClientRegistrationStep2View.as_view(), name='client_register_step2'),
    path('client/register/success/', views.RegistrationSuccessView.as_view(), name='client_register_success'),
    
    # Password Management
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password/reset.html',
             email_template_name='accounts/password/reset_email.html',
             success_url='done/'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password/reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password/reset_confirm.html',
             success_url='/password-reset/complete/'
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password/reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # User Profiles
    #path('profile/edit/', views.ClientProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/notifications/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
    
    # Dashboards
    path('dashboard/client/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('dashboard/interpreter/', views.InterpreterDashboardView.as_view(), name='interpreter_dashboard'),
    
    # Quote Management (Client)
    path('client/quotes/', views.QuoteRequestListView.as_view(), name='client_quote_list'),
    path('client/quotes/create/', views.QuoteRequestCreateView.as_view(), name='client_quote_create'),
    path('client/quotes/<int:pk>/', views.QuoteRequestDetailView.as_view(), name='client_quote_detail'),
    path('client/quotes/<int:pk>/accept/', views.QuoteAcceptView.as_view(), name='client_quote_accept'),
    path('client/quotes/<int:pk>/reject/', views.QuoteRejectView.as_view(), name='client_quote_reject'),
    
    # Assignment Management (Client)
    path('client/assignments/<int:pk>/', views.AssignmentDetailClientView.as_view(), name='client_assignment_detail'),
    
    path('clienprofile/', views.ProfileView.as_view(), name='client_profile_edit'),
    path('client_profile/password/', views.ProfilePasswordChangeView.as_view(), name='client_change_password'),
    
    #interpreter
        path(
        'interpreter/register/', 
        views.InterpreterRegistrationStep1View.as_view(), 
        name='interpreter_registration_step1'
    ),
    path(
        'interpreter/register/step2/', 
        views.InterpreterRegistrationStep2View.as_view(), 
        name='interpreter_registration_step2'
    ),
    path(
        'interpreter/register/step3/', 
        views.InterpreterRegistrationStep3View.as_view(), 
        name='interpreter_registration_step3'
    ),
  path('interpreter/settings/', 
    views.InterpreterSettingsView.as_view(), 
    name='interpreter_settings'),
    
    path(
        'interpreter/schedule/',
        views.InterpreterScheduleView.as_view(),
        name='interpreter_schedule'
    ),
    path(
        'interpreter/schedule/assignments/',
        views.get_calendar_assignments,
        name='get_calendar_assignments'
    ),
        path(
        'interpreter/assignments/',
        views.AssignmentListView.as_view(),
        name='interpreter_assignments'
    ),
    path(
        'interpreter/assignments/<int:pk>/',
        views.AssignmentDetailView.as_view(),
        name='assignment_detail'
    ),
    path(
        'interpreter/assignments/<int:pk>/accept/',
        views.accept_assignment,
        name='accept_assignment'
    ),
    path(
        'interpreter/assignments/<int:pk>/reject/',
        views.reject_assignment,
        name='reject_assignment'
    ),
    path(
        'interpreter/assignments/<int:pk>/complete/',
        views.complete_assignment,
        name='complete_assignment'
    ),
        path(
        'interpreter/earnings/',
        views.TranslatorEarningsView.as_view(),
        name='translator_earnings'
    ),
    path(
        'interpreter/earnings/data/',
        views.get_earnings_data,
        name='earnings_data'
    ),
    path(
        'interpreter/earnings/data/<int:year>/',
        views.get_earnings_data,
        name='earnings_data_year'
    ),

    # API endpoints
    path('api/notifications/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('api/notifications/clear-all/', views.ClearAllNotificationsView.as_view(), name='clear_all_notifications'),
    
]