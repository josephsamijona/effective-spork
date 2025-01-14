# forms.py
from django import forms
from .models import PublicQuoteRequest, ServiceType

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