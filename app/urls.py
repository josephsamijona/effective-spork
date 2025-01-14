# urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'dbdint'

urlpatterns = [
    # Public Pages
    path('', views.PublicQuoteRequestView.as_view(), name='home'),
    path('request-quote/success/', views.QuoteRequestSuccessView.as_view(), name='quote_request_success'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/success/', views.ContactSuccessView.as_view(), name='contact_success'),

    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dbdint:home'), name='logout'),
    
    # Client Registration
    path('register/', views.ClientRegistrationView.as_view(), name='register'),
    path('register/step2/', views.ClientRegistrationStep2View.as_view(), name='register_step2'),
    path('register/success/', views.RegistrationSuccessView.as_view(), name='register_success'),
    
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
    path('profile/edit/', views.ClientProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/notifications/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
    
    # Dashboards
    path('dashboard/client/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    path('dashboard/interpreter/', views.InterpreterDashboardView.as_view(), name='interpreter_dashboard'),
    
    # Quote Management (Client)
    path('quotes/', views.QuoteRequestListView.as_view(), name='quote_list'),
    path('quotes/create/', views.QuoteRequestCreateView.as_view(), name='quote_create'),
    path('quotes/<int:pk>/', views.QuoteRequestDetailView.as_view(), name='quote_detail'),
    path('quotes/<int:pk>/accept/', views.QuoteAcceptView.as_view(), name='quote_accept'),
    path('quotes/<int:pk>/reject/', views.QuoteRejectView.as_view(), name='quote_reject'),
    
    # Assignment Management (Client)
    path('assignments/<int:pk>/', views.AssignmentDetailClientView.as_view(), name='assignment_detail'),
    
    # API endpoints
    path('api/notifications/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('api/notifications/clear-all/', views.ClearAllNotificationsView.as_view(), name='clear_all_notifications'),
]