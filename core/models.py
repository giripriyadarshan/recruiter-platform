from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import json
from django.core.exceptions import ValidationError
from django.db.models import signals
from django.dispatch import receiver


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where username is the unique identifier.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        """
        Create and save a user with the given username, email and password.
        """
        if not username:
            raise ValueError(_('The Username must be set'))
        if not email:
            raise ValueError(_('The Email must be set'))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given username, email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model that uses username as the unique identifier.
    """
    email = models.EmailField(_('email address'), unique=True)
    full_name = models.CharField(_('full name'), max_length=255, blank=True)
    is_candidate = models.BooleanField(default=False)
    is_hiring_manager = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return self.username


class Candidate(models.Model):
    """
    Model representing a candidate in the recruitment process.
    """
    SOURCE_CHOICES = [
        ('GITHUB', 'GitHub'),
        ('STACK_OVERFLOW', 'Stack Overflow'),
        ('OTHER', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='DIRECT')
    source_score = models.IntegerField(default=0)
    resume_url = models.URLField(blank=True, null=True)
    profile_completed = models.BooleanField(default=False)
    skills = models.TextField(blank=True)
    generated_password = models.CharField(max_length=255, blank=True, null=True, help_text=_(
        'Temporary storage for generated password. Clear after first login.'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    INTERVIEW_STATUS_CHOICES = [
        ('PENDING', 'Pending Decision'),
        ('ACCEPTED', 'Accepted for Interview'),
        ('REJECTED', 'Rejected'),
    ]

    interview_status = models.CharField(
        max_length=20,
        choices=INTERVIEW_STATUS_CHOICES,
        default='PENDING',
    )
    interview_decision_date = models.DateTimeField(null=True, blank=True)
    interview_notes = models.TextField(blank=True, null=True)
    interview_date = models.DateTimeField(null=True, blank=True)

    # Track GDPR data cleanup status
    data_cleanup_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active Data'),
            ('MARKED_FOR_DELETION', 'Marked for Deletion'),
            ('ANONYMIZED', 'Data Anonymized'),
        ],
        default='ACTIVE',
    )

    def __str__(self):
        return f"Candidate: {self.user.username}"

    class Meta:
        ordering = ['-created_at']


class HiringManager(models.Model):
    """
    Model representing a hiring manager who can create and evaluate assessments.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hiring_manager_profile')
    company_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    can_create_assessments = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hiring Manager: {self.user.username} ({self.company_name})"

    class Meta:
        ordering = ['company_name', '-created_at']


# Add this new model to your existing models.py

class CodingQuestion(models.Model):
    """
    Model to store LeetCode-style coding questions.
    """
    QUESTION_TYPE_CHOICES = [
        ('FRONTEND', 'Frontend Development'),
        ('BACKEND', 'Backend Development'),
        ('DATABASE', 'Database Design'),
    ]

    DIFFICULTY_CHOICES = [
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='MEDIUM')

    # Example input/output and constraints
    example_input = models.TextField(blank=True)
    example_output = models.TextField(blank=True)
    constraints = models.TextField(blank=True)

    # Starter code in different languages
    starter_code_python = models.TextField(blank=True)
    starter_code_javascript = models.TextField(blank=True)
    starter_code_sql = models.TextField(blank=True)
    starter_code_html = models.TextField(blank=True)
    starter_code_css = models.TextField(blank=True)

    # Testing functions or expected results
    test_cases = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_question_type_display()} - {self.get_difficulty_display()})"

    def get_starter_code(self, language):
        """
        Get the starter code for a specific language
        """
        if language == 'python':
            return self.starter_code_python
        elif language == 'javascript':
            return self.starter_code_javascript
        elif language == 'sql':
            return self.starter_code_sql
        elif language == 'html':
            return self.starter_code_html
        elif language == 'css':
            return self.starter_code_css
        return ""

class Assessment(models.Model):
    """
    Model representing a coding assessment instance.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent to Candidate'),
        ('ACCEPTED', 'Accepted by Candidate'),
        ('STARTED', 'Started'),
        ('FINISHED', 'Finished'),
        ('SCORING', 'Being Scored'),
        ('SCORED', 'Scored'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    QUESTION_TYPE_CHOICES = [
        ('FRONTEND', 'Frontend Development'),
        ('BACKEND', 'Backend Development'),
        ('DATABASE', 'Database Design'),
        ('FULLSTACK', 'Full Stack'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='assessments')
    created_by = models.ForeignKey(HiringManager, on_delete=models.SET_NULL, null=True,
                                   related_name='created_assessments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Assessment scheduling and timeframe
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=120)  # 2 hours default

    # Assessment status and scoring
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    score = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    # Questions
    question_frontend = models.TextField(blank=True)
    question_backend = models.TextField(blank=True)
    question_database = models.TextField(blank=True)
    chosen_question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, null=True, blank=True)

    # Personality assessment
    personality_questions = models.JSONField(null=True, blank=True)
    personality_answers = models.JSONField(null=True, blank=True)

    # Code submission
    code_submission = models.TextField(blank=True)
    # code_language = models.CharField(max_length=50, blank=True)

    accepted_at = models.DateTimeField(null=True, blank=True)
    invite_expires_at = models.DateTimeField(null=True, blank=True)
    assessment_url_token = models.CharField(max_length=64, null=True, blank=True)

    # New fields for the question system
    available_questions = models.ManyToManyField(CodingQuestion, blank=True, related_name='assessments')
    chosen_question = models.ForeignKey(
        CodingQuestion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='chosen_assessments'
    )

    # Field to track which language the candidate is using
    code_language = models.CharField(max_length=50, blank=True, default='python')

    evaluation_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Evaluation'),
            ('EVALUATING', 'Evaluation in Progress'),
            ('EVALUATED', 'Evaluation Complete'),
            ('FAILED', 'Evaluation Failed'),
        ],
        default='PENDING',
        null=True,
        blank=True,
    )
    evaluation_score = models.FloatField(null=True, blank=True)
    evaluation_results = models.JSONField(null=True, blank=True)
    evaluation_started_at = models.DateTimeField(null=True, blank=True)
    evaluation_completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Assessment for {self.candidate.user.username} - {self.status}"

    def is_expired(self):
        """Check if the assessment has expired."""
        if not self.sent_at:
            return False
        expiry_period = timezone.timedelta(days=7)  # Assessments expire after 7 days
        return timezone.now() > (self.sent_at + expiry_period)

    def time_remaining(self):
        """Calculate remaining time in minutes if assessment is in progress."""
        if self.status != 'STARTED' or not self.start_time:
            return None

        elapsed = timezone.now() - self.start_time
        remaining_seconds = (self.time_limit_minutes * 60) - elapsed.total_seconds()
        return max(0, int(remaining_seconds / 60))  # Return minutes remaining

    def save(self, *args, **kwargs):
        # Generate a unique token for assessment URL when created
        if not self.assessment_url_token:
            import uuid
            self.assessment_url_token = uuid.uuid4().hex

        # Set invitation expiry date when status changes to SENT
        if self.status == 'SENT' and not self.invite_expires_at and self.sent_at:
            self.invite_expires_at = self.sent_at + timezone.timedelta(days=7)

        # When the assessment starts, set the end time to 24 hours later
        if self.status == 'STARTED' and self.start_time and not self.end_time:
            self.end_time = self.start_time + timezone.timedelta(hours=24)

        super().save(*args, **kwargs)

    def is_invite_expired(self):
        """Check if the assessment invitation has expired."""
        if not self.invite_expires_at:
            return False
        return timezone.now() > self.invite_expires_at

    def is_in_progress(self):
        """Check if the assessment is currently in progress."""
        return self.status == 'STARTED' and self.start_time and timezone.now() < self.end_time

    def is_time_up(self):
        """Check if the assessment time limit has been reached."""
        if not self.start_time or not self.end_time:
            return False
        return timezone.now() > self.end_time

    def time_remaining(self):
        """Calculate remaining time in hours and minutes if assessment is in progress."""
        if not self.is_in_progress():
            return None

        remaining = self.end_time - timezone.now()
        total_seconds = max(0, remaining.total_seconds())
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        return {
            'hours': hours,
            'minutes': minutes,
            'total_seconds': int(total_seconds)
        }

    def progress_percentage(self):
        """Calculate the progress percentage (time used vs total time)."""
        if not self.start_time or not self.end_time:
            return 0

        if self.is_time_up():
            return 100

        total_duration = (self.end_time - self.start_time).total_seconds()
        elapsed = (timezone.now() - self.start_time).total_seconds()
        percentage = min(100, (elapsed / total_duration) * 100)

        return round(percentage, 1)

    class Meta:
        ordering = ['-created_at']