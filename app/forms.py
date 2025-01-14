# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm
from .models import User, Client, NotificationPreference, Language

from .models import PublicQuoteRequest, ServiceType, ContactMessage

class PublicQuoteRequestForm(forms.ModelForm):
    class Meta:
        model = PublicQuoteRequest
        fields = [
            'full_name', 'email', 'phone', 'company_name',
            'source_language', 'target_language', 'service_type',
            'requested_date', 'duration', 'location', 'city', 
            'state', 'zip_code', 'special_requirements'
        ]
        widgets = {
            'requested_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'special_requirements': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Please provide any additional details or special requirements...'
                }
            ),
            'full_name': forms.TextInput(
                attrs={'placeholder': 'Enter your full name'}
            ),
            'email': forms.EmailInput(
                attrs={'placeholder': 'Enter your email address'}
            ),
            'phone': forms.TextInput(
                attrs={'placeholder': '(123) 456-7890'}
            ),
            'company_name': forms.TextInput(
                attrs={'placeholder': 'Enter your company name'}
            ),
            'location': forms.TextInput(
                attrs={'placeholder': 'Enter the service location'}
            ),
            'duration': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter duration in minutes',
                    'min': '30',
                    'step': '15'
                }
            ),
            'service_type': forms.Select(
                attrs={'class': 'form-control'}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required except special_requirements
        for field_name, field in self.fields.items():
            if field_name != 'special_requirements':
                field.required = True
        
        # Only show active services in the dropdown
        self.fields['service_type'].queryset = ServiceType.objects.filter(active=True)
        
        # Optional: Customize the empty label
        self.fields['service_type'].empty_label = "Select a service type"
        
        
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Message Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Your Message'
            })
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email:
            raise forms.ValidationError("Email is required")
        return email
    
    
    
################################client
# forms.py

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password'
    }))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

class ClientRegistrationForm1(forms.ModelForm):
    """First step: Basic user information"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            })
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered")
        return email

class ClientRegistrationForm2(forms.ModelForm):
    """Second step: Company information"""
    class Meta:
        model = Client
        fields = ['company_name', 'address', 'city', 'state', 'zip_code', 'preferred_language']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ZIP code'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_language'].queryset = Language.objects.filter(is_active=True)

class ClientProfileUpdateForm(forms.ModelForm):
    """Form for updating client profile"""
    class Meta:
        model = Client
        exclude = ['user', 'created_at', 'active']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_address': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_city': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_state': forms.TextInput(attrs={'class': 'form-control'}),
            'billing_zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_language': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        exclude = ['user']
        widgets = {
            'email_quote_updates': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_assignment_updates': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_payment_updates': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'quote_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'assignment_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'payment_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'system_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notification_frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_language'].queryset = Language.objects.filter(is_active=True)

class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with styling"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )