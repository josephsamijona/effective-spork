import os
import django

# Django environment setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import ServiceType

def update_service_types():
    # First, delete all existing services
    ServiceType.objects.all().delete()
    print("All existing services have been deleted.")

    # Define new services with explicit names
    services = [
        {
            'name': 'Document Translation',
            'description': (
                'Professional document translation service. '
                'We translate all types of documents: administrative, legal, '
                'medical, technical, commercial, etc. Each translation is '
                'reviewed by a second translator to ensure quality.'
            ),
            'base_rate': 0.25,  # Price per word
            'minimum_hours': 1,
            'cancellation_policy': (
                'Any translation project that has begun is due for the work completed. '
                'Cancellation of a project before it starts is free if it occurs '
                'within 24 hours of quote acceptance.'
            ),
            'requires_certification': True,
            'active': True
        },
        {
            'name': 'On-Site Interpretation',
            'description': (
                'In-person interpretation service for your meetings, conferences, '
                'medical appointments, or legal proceedings. Our interpreters travel '
                'to your location to ensure smooth and professional communication.'
            ),
            'base_rate': 95.00,
            'minimum_hours': 2,
            'cancellation_policy': (
                'Free cancellation up to 48 hours before the service. '
                '50% of total amount charged between 48 and 24 hours before the service. '
                '100% of total amount charged for cancellations less than 24 hours before.'
            ),
            'requires_certification': False,
            'active': True
        },
        {
            'name': 'Phone Interpretation',
            'description': (
                '24/7 telephone interpretation service. Ideal for '
                'urgent or short communications. Quick connection with '
                'a professional interpreter within minutes.'
            ),
            'base_rate': 65.00,
            'minimum_hours': 1,
            'cancellation_policy': (
                'Service billed by the minute after the first minute. '
                'No cancellation fee before connecting with the interpreter.'
            ),
            'requires_certification': False,
            'active': True
        },
        {
            'name': 'Video Interpretation',
            'description': (
                'Online interpretation service via major video conferencing platforms '
                '(Zoom, Teams, Google Meet, etc.). Perfect for remote meetings, '
                'online training sessions, or virtual consultations.'
            ),
            'base_rate': 85.00,
            'minimum_hours': 1,
            'cancellation_policy': (
                'Free cancellation up to 24 hours before the service. '
                '50% of total amount charged between 24 and 12 hours before the service. '
                '100% of total amount charged for cancellations less than 12 hours before.'
            ),
            'requires_certification': False,
            'active': True
        }
    ]

    print("Creating new services with explicit names...")
    for service_data in services:
        try:
            service = ServiceType.objects.create(**service_data)
            print(f"Service created: {service.name}")
        except Exception as e:
            print(f"Error creating service {service_data['name']}: {str(e)}")

    print(f"\nCompleted! {len(services)} services have been configured in the database.")
    
    # Display all services for verification
    print("\nCurrent services in database:")
    for service in ServiceType.objects.all().order_by('id'):
        print(f"ID: {service.id}, Name: {service.name}")

if __name__ == '__main__':
    # Confirmation before proceeding
    print("WARNING: This script will delete all existing services and create new ones.")
    print("This action cannot be undone.")
    response = input("Do you want to continue? (y/n): ")
    
    if response.lower() == 'y':
        update_service_types()
    else:
        print("Operation cancelled.")