from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('dept_sender_receiver', 'Dept. Sender/Receiver'),
        ('dept_head', 'Dept. Head'),
        ('governor', 'Governor'),
        ('executive', 'Executive'),
    ]
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='dept_sender_receiver')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Document(models.Model):
    SOURCE_CHOICES = [('internal', 'Internal'), ('external', 'External')]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('esigned', 'E-Signed'),
        ('released', 'Released to Correspondent'),
        ('returned', 'Returned to Origin'),
        ('archived', 'Archived'),
        ('return_for_revision', 'Returned for Revision'),
    ]
    ACTION_TYPE_CHOICES = [('return', 'Return to Origin'), ('release', 'Release to External Agency')]
    CLASSIFICATION_CHOICES = [
        ('confidential', 'Confidential'),
        ('internal', 'Internal Use Only'),
        ('public', 'Public'),
    ]

    title = models.CharField(max_length=300)
    reference_number = models.CharField(max_length=100, unique=True, blank=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, default='internal')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    action_type = models.CharField(max_length=10, choices=ACTION_TYPE_CHOICES, blank=True, null=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/%Y/%m/', blank=True, null=True)
    esignature = models.ImageField(upload_to='signatures/%Y/%m/', blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_documents')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_documents')
    origin_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='origin_documents')
    current_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_documents')
    correspondent_name = models.CharField(max_length=200, blank=True)
    correspondent_agency = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logged_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.reference_number:
            from django.utils.timezone import now
            count = Document.objects.count() + 1
            self.reference_number = f"DOC-{now().year}-{count:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_number}: {self.title}"


class DocumentRouting(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='routings')
    from_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='sent_routings')
    to_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='received_routings')
    forwarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    forwarded_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.document} → {self.to_department}"


class DocumentLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('logged', 'Logged'),
        ('classified', 'Classified'),
        ('assigned', 'Assigned to Action Officer'),
        ('processed', 'Processed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('esigned', 'E-Signed'),
        ('routed', 'Routed to Next Office'),
        ('released', 'Released'),
        ('returned', 'Returned'),
        ('archived', 'Archived'),
        ('revision', 'Returned for Revision'),
        ('notified', 'Parties Notified'),
    ]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.document} - {self.get_action_display()} by {self.user}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif for {self.recipient}: {self.message[:50]}"
