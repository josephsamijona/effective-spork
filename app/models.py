from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # ISO code
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class User(AbstractUser):
    class Roles(models.TextChoices):
        CLIENT = 'CLIENT', _('Client')
        INTERPRETER = 'INTERPRETER', _('Interprète')
        ADMIN = 'ADMIN', _('Administrateur')

    # Ajout des related_name pour éviter les conflits
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set'  # Ajout du related_name personnalisé
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set'  # Ajout du related_name personnalisé
    )

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Roles.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    registration_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    billing_address = models.TextField(blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_state = models.CharField(max_length=50, blank=True, null=True)
    billing_zip_code = models.CharField(max_length=20, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    preferred_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

class InterpreterLanguage(models.Model):
    class Proficiency(models.TextChoices):
        NATIVE = 'NATIVE', _('Natif')
        FLUENT = 'FLUENT', _('Courant')
        PROFESSIONAL = 'PROFESSIONAL', _('Professionnel')
        INTERMEDIATE = 'INTERMEDIATE', _('Intermédiaire')

    interpreter = models.ForeignKey('Interpreter', on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    proficiency = models.CharField(max_length=20, choices=Proficiency.choices)
    is_primary = models.BooleanField(default=False)
    certified = models.BooleanField(default=False)
    certification_details = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['interpreter', 'language']

class Interpreter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='interpreter_profile')
    languages = models.ManyToManyField(Language, through=InterpreterLanguage)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    certifications = models.JSONField(null=True, blank=True)  # Format: [{"name": "CCHI", "expiry_date": "2025-01-01"}]
    specialties = models.JSONField(null=True, blank=True)  # Format: ["Medical", "Legal"]
    availability = models.JSONField(null=True, blank=True)  # Format: {"monday": ["9:00-17:00"]}
    radius_of_service = models.IntegerField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Informations bancaires pour ACH
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_holder_name = models.CharField(max_length=100, null=True, blank=True)
    routing_number = models.CharField(max_length=9, null=True, blank=True)
    account_number = models.CharField(max_length=17, null=True, blank=True)
    account_type = models.CharField(
        max_length=10, 
        choices=[('checking', 'Checking'), ('savings', 'Savings')],
        null=True,
        blank=True
    )
    
    background_check_date = models.DateField(null=True, blank=True)
    background_check_status = models.BooleanField(default=False)
    w9_on_file = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

# models.py
class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_hours = models.IntegerField(default=1)
    cancellation_policy = models.TextField()
    requires_certification = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class QuoteRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        PROCESSING = 'PROCESSING', _('En cours de traitement')
        QUOTED = 'QUOTED', _('Devis envoyé')
        ACCEPTED = 'ACCEPTED', _('Accepté')
        REJECTED = 'REJECTED', _('Rejeté')
        EXPIRED = 'EXPIRED', _('Expiré')

    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    requested_date = models.DateTimeField()
    duration = models.IntegerField(help_text="Durée en minutes")
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    source_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='quote_requests_source')
    target_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='quote_requests_target')
    special_requirements = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Quote(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', _('Brouillon')
        SENT = 'SENT', _('Envoyé')
        ACCEPTED = 'ACCEPTED', _('Accepté')
        REJECTED = 'REJECTED', _('Rejeté')
        EXPIRED = 'EXPIRED', _('Expiré')
        CANCELLED = 'CANCELLED', _('Annulé')

    quote_request = models.OneToOneField(QuoteRequest, on_delete=models.PROTECT)
    reference_number = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_until = models.DateField()
    terms = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Assignment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        ASSIGNED = 'ASSIGNED', _('Assigné')
        CONFIRMED = 'CONFIRMED', _('Confirmé')
        IN_PROGRESS = 'IN_PROGRESS', _('En cours')
        COMPLETED = 'COMPLETED', _('Terminé')
        CANCELLED = 'CANCELLED', _('Annulé')
        NO_SHOW = 'NO_SHOW', _('Non présentation')

    quote = models.OneToOneField(Quote, on_delete=models.PROTECT, null=True, blank=True)
    interpreter = models.ForeignKey(Interpreter, on_delete=models.PROTECT)
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    source_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='assignments_source')
    target_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='assignments_target')
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=Status.choices)
    
    # Informations financières
    interpreter_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Taux horaire de l'interprète")
    minimum_hours = models.IntegerField(default=2)
    total_interpreter_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class AssignmentFeedback(models.Model):
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('En attente')
        COMPLETED = 'COMPLETED', _('Complété')
        FAILED = 'FAILED', _('Échoué')
        REFUNDED = 'REFUNDED', _('Remboursé')

    class PaymentType(models.TextChoices):
        CLIENT_PAYMENT = 'CLIENT_PAYMENT', _('Paiement client')
        INTERPRETER_PAYMENT = 'INTERPRETER_PAYMENT', _('Paiement interprète')

    quote = models.ForeignKey(Quote, on_delete=models.PROTECT, null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    payment_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

class Notification(models.Model):
    class Type(models.TextChoices):
        QUOTE_REQUEST = 'QUOTE_REQUEST', _('Demande de devis')
        QUOTE_READY = 'QUOTE_READY', _('Devis prêt')
        ASSIGNMENT_OFFER = 'ASSIGNMENT_OFFER', _('Offre de mission')
        ASSIGNMENT_REMINDER = 'ASSIGNMENT_REMINDER', _('Rappel de mission')
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', _('Paiement reçu')
        SYSTEM = 'SYSTEM', _('Système')

    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=200)
    content = models.TextField()
    read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    
class PublicQuoteRequest(models.Model):
    # Contact Information
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company_name = models.CharField(max_length=100)
    
    # Service Details
    source_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='public_quotes_source')
    target_language = models.ForeignKey(Language, on_delete=models.PROTECT, related_name='public_quotes_target')
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
    requested_date = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    
    # Location
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    
    # Additional Information
    special_requirements = models.TextField(blank=True, null=True)
    
    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Quote Request from {self.full_name} ({self.company_name})"

# models.py

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email Notifications
    email_quote_updates = models.BooleanField(default=True, help_text="Receive email notifications about quote status updates")
    email_assignment_updates = models.BooleanField(default=True, help_text="Receive email notifications about assignment updates")
    email_payment_updates = models.BooleanField(default=True, help_text="Receive email notifications about payment status")
    
    # SMS Notifications (si implémenté dans le futur)
    sms_enabled = models.BooleanField(default=False, help_text="Enable SMS notifications")
    
    # In-App Notifications
    quote_notifications = models.BooleanField(default=True, help_text="Receive in-app notifications about quotes")
    assignment_notifications = models.BooleanField(default=True, help_text="Receive in-app notifications about assignments")
    payment_notifications = models.BooleanField(default=True, help_text="Receive in-app notifications about payments")
    system_notifications = models.BooleanField(default=True, help_text="Receive system notifications and updates")

    # Communication Preferences
    preferred_language = models.ForeignKey(
        Language, 
        on_delete=models.SET_NULL, 
        null=True, 
        help_text="Preferred language for notifications"
    )
    
    # Notification Frequency
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest')
        ],
        default='immediate',
        help_text="How often to receive notifications"
    )

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Notification preferences for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.preferred_language and self.user.client_profile:
            self.preferred_language = self.user.client_profile.preferred_language
        super().save(*args, **kwargs)