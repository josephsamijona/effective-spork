import os
import django
import random
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta
from faker import Faker

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.models import (
    User, Client, Interpreter, InterpreterLanguage, ServiceType, 
    QuoteRequest, Quote, Assignment, AssignmentFeedback, Payment,
    Notification, NotificationPreference, Language
)

fake = Faker(['en_US'])
credentials = []

def generate_phone():
    """Generate a US format phone number"""
    return f"+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

def clean_database():
    print("Cleaning database...")
    Payment.objects.all().delete()
    AssignmentFeedback.objects.all().delete()
    Assignment.objects.all().delete()
    Quote.objects.all().delete()
    QuoteRequest.objects.all().delete()
    Notification.objects.all().delete()
    NotificationPreference.objects.all().delete()
    InterpreterLanguage.objects.all().delete()
    Client.objects.all().delete()
    Interpreter.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()

def create_users(role, count):
    print(f"Creating {count} {role} users...")
    users = []
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        username = f"{first_name.lower()}{last_name.lower()}"
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password('password123'),
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone=generate_phone(),
            is_active=True,
            registration_complete=True
        )
        
        credentials.append({
            'role': role,
            'username': username,
            'email': email,
            'password': 'password123'
        })
        
        users.append(user)
    return users

def create_client_profiles(clients):
    print("Creating client profiles...")
    languages = Language.objects.all()
    
    for client in clients:
        Client.objects.create(
            user=client,
            company_name=fake.company(),
            address=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            zip_code=fake.zipcode(),
            preferred_language=random.choice(languages),
            credit_limit=Decimal(random.randint(1000, 10000)),
            active=True
        )

def create_interpreter_profiles(interpreters):
    print("Creating interpreter profiles...")
    languages = Language.objects.all()
    specialties = ["Medical", "Legal", "Technical", "Conference", "Financial"]
    
    for interpreter in interpreters:
        interpreter_profile = Interpreter.objects.create(
            user=interpreter,
            bio=fake.text(max_nb_chars=200),
            address=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            zip_code=fake.zipcode(),
            hourly_rate=Decimal(random.randint(50, 150)),
            radius_of_service=random.randint(20, 100),
            specialties=random.sample(specialties, random.randint(1, 3)),
            background_check_status=True,
            active=True
        )
        
        selected_languages = random.sample(list(languages), random.randint(2, 4))
        for lang in selected_languages:
            InterpreterLanguage.objects.create(
                interpreter=interpreter_profile,
                language=lang,
                proficiency=random.choice(['NATIVE', 'FLUENT', 'PROFESSIONAL']),
                certified=random.choice([True, False])
            )

def create_assignments(clients, interpreters):
    print("Creating assignments...")
    service_types = ServiceType.objects.all()
    languages = Language.objects.all()
    
    for _ in range(30):
        client = random.choice(clients)
        interpreter = random.choice(interpreters)
        source_lang, target_lang = random.sample(list(languages), 2)
        status = random.choice(['PENDING', 'ASSIGNED', 'CONFIRMED', 'COMPLETED'])
        
        start_time = fake.future_datetime(end_date='+60d')
        end_time = start_time + timedelta(hours=random.randint(1, 4))
        
        assignment = Assignment.objects.create(
            interpreter=interpreter.interpreter_profile,
            client=client.client_profile,
            service_type=random.choice(service_types),
            source_language=source_lang,
            target_language=target_lang,
            start_time=start_time,
            end_time=end_time,
            location=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            zip_code=fake.zipcode(),
            status=status,
            interpreter_rate=Decimal(random.randint(50, 150)),
            minimum_hours=2
        )
        
        if status == 'COMPLETED':
            AssignmentFeedback.objects.create(
                assignment=assignment,
                rating=random.randint(3, 5),
                comments=fake.text(),
                created_by=client
            )
            
            Payment.objects.create(
                assignment=assignment,
                payment_type='CLIENT_PAYMENT',
                amount=assignment.interpreter_rate * Decimal(assignment.minimum_hours),
                payment_method='CREDIT_CARD',
                transaction_id=fake.uuid4(),
                status='COMPLETED'
            )

def save_credentials():
    print("Saving credentials...")
    with open('credentials.txt', 'w') as f:
        f.write("TEST CREDENTIALS\n")
        f.write("================\n\n")
        
        current_role = None
        for cred in sorted(credentials, key=lambda x: (x['role'], x['username'])):
            if current_role != cred['role']:
                current_role = cred['role']
                f.write(f"\n{current_role} USERS\n")
                f.write("-" * (len(current_role) + 6) + "\n\n")
            
            f.write(f"Username: {cred['username']}\n")
            f.write(f"Email: {cred['email']}\n")
            f.write(f"Password: {cred['password']}\n")
            f.write("-" * 30 + "\n")

def main():
    print("Starting database population...")
    
    try:
        with transaction.atomic():
            clean_database()
            
            clients = create_users('CLIENT', 10)
            interpreters = create_users('INTERPRETER', 10)
            admins = create_users('ADMIN', 10)
            
            create_client_profiles(clients)
            create_interpreter_profiles(interpreters)
            create_assignments(clients, interpreters)
            
            save_credentials()
            
        print("Database population completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    main()