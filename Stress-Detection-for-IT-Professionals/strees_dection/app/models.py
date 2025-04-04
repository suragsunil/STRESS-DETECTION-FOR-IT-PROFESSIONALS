from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User

# UsersRegister Model
class UsersRegister(models.Model):
    first_name = models.CharField(max_length=100, null=True, help_text="User's first name")
    last_name = models.CharField(max_length=100, null=True, help_text="User's last name")
    email_id = models.EmailField(unique=True, null=True, blank=True, help_text="User's email address")
    password = models.CharField(max_length=100, null=True, blank=True, help_text="User's password")
    confirm_password = models.CharField(max_length=100, null=True, blank=True, help_text="Confirm user's password")
    image = models.ImageField(upload_to='media', null=True, blank=True, help_text="Profile picture of the user")
    department = models.CharField(max_length=100, null=True, blank=True, help_text="Department of the user (e.g., IT, HR, etc.)")
    years_of_experience = models.PositiveIntegerField(null=True, blank=True, help_text="Years of experience in the work role")
    work_role = models.CharField(max_length=100, null=True, blank=True, help_text="Work role or job title (e.g., Software Engineer, Manager)")

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email_id}"

# StressAssessment Model
class StressAssessment(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(default=now)
    responses = models.JSONField()
    stress_score = models.IntegerField()
    recommendations = models.TextField()

    def __str__(self):
        return f"Assessment on {self.date} - Score: {self.stress_score}"

# Feedback Model
class Feedback(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    assessment = models.ForeignKey(StressAssessment, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    rating = models.IntegerField()
    date = models.DateTimeField(default=now)

    def __str__(self):
        return f"Feedback by {self.user.email_id} on {self.date}"

# Models for Data Collection Module

# Behavioral Data Collector Models
class KeyboardActivity(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    keystrokes_per_minute = models.IntegerField(help_text="Number of keystrokes per minute")
    typing_duration = models.DurationField(help_text="Duration of typing activity")

    def __str__(self):
        return f"Keyboard Activity for {self.user.email_id} at {self.timestamp}"

class ScreenTime(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    duration = models.DurationField(help_text="Total screen time duration")
    application = models.CharField(max_length=100, null=True, blank=True, help_text="Application in focus")

    def __str__(self):
        return f"Screen Time for {self.user.email_id} at {self.timestamp}"

class ApplicationUsage(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    app_name = models.CharField(max_length=100, help_text="Name of the application")
    usage_duration = models.DurationField(help_text="Duration of app usage")

    def __str__(self):
        return f"App Usage: {self.app_name} by {self.user.email_id} at {self.timestamp}"

class VoicePattern(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    audio_file = models.FileField(upload_to='voice_patterns/', null=True, blank=True, help_text="Recorded voice sample")
    stress_level = models.FloatField(null=True, blank=True, help_text="Estimated stress level from voice analysis")

    def __str__(self):
        return f"Voice Pattern for {self.user.email_id} at {self.timestamp}"

# Wearable Device Integration Model
class WearableData(models.Model):
    DEVICE_TYPES = (
        ('FITBIT', 'Fitbit'),
        ('APPLE_WATCH', 'Apple Watch'),
        ('OTHER', 'Other'),
    )
    
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, help_text="Type of wearable device")
    timestamp = models.DateTimeField(default=now)
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Heart rate in beats per minute")
    steps = models.IntegerField(null=True, blank=True, help_text="Number of steps taken")
    sleep_duration = models.DurationField(null=True, blank=True, help_text="Sleep duration")
    stress_indicator = models.FloatField(null=True, blank=True, help_text="Stress indicator from wearable data")

    def __str__(self):
        return f"Wearable Data from {self.device_type} for {self.user.email_id} at {self.timestamp}"
# Recommendation sections

class Recommendation(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    stress_assessment = models.ForeignKey(StressAssessment, on_delete=models.CASCADE, null=True, blank=True)
    recommendation_text = models.TextField(help_text="Personalized recommendation content")
    category = models.CharField(max_length=50, choices=[
        ('BREAK', 'Take a Break'),
        ('EXERCISE', 'Exercise'),
        ('MINDFULNESS', 'Mindfulness'),
        ('SCHEDULE', 'Schedule Adjustment'),
        ('RESOURCE', 'Resource'),
    ])
    priority = models.IntegerField(default=1, help_text="Priority level (1-5)")
    created_at = models.DateTimeField(auto_now_add=True)  # Changed to auto_now_add
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category} Recommendation for {self.user.email_id}"
    
class Alert(models.Model):
    user = models.ForeignKey(UsersRegister, on_delete=models.CASCADE)
    message = models.TextField(help_text="Alert message for high stress")
    threshold = models.IntegerField(help_text="Stress score threshold that triggered this alert")
    triggered_at = models.DateTimeField(auto_now_add=True)  # Changed to auto_now_add
    is_acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert for {self.user.email_id} at {self.triggered_at}"

class Resource(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('VIDEO', 'Video'),
        ('ARTICLE', 'Article'),
        ('AUDIO', 'Audio'),
        ('EXERCISE', 'Exercise'),
    ])
    url = models.URLField(null=True, blank=True)
    file = models.FileField(upload_to='resources/', null=True, blank=True)

    def __str__(self):
        return self.title