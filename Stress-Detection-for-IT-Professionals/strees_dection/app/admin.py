from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
import csv
from .models import (
    UsersRegister, StressAssessment, Feedback,
    KeyboardActivity, ScreenTime, ApplicationUsage, VoicePattern, WearableData,
    Recommendation, Alert, Resource  # Newly added models
)

# Custom admin for UsersRegister
class UsersRegisterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email_id', 'department', 'years_of_experience', 'work_role', 'profile_pic')
    search_fields = ('first_name', 'last_name', 'email_id', 'department')
    list_filter = ('department', 'years_of_experience')

    def profile_pic(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%"/>', obj.image.url)
        return "No Image"
    profile_pic.short_description = 'Profile Picture'

# Custom admin for StressAssessment
class StressAssessmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'stress_score', 'recommendations')
    search_fields = ('date', 'user__email_id')
    list_filter = ('stress_score',)

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stress_assessments.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Date', 'Stress Score', 'Recommendations'])
        
        assessments = StressAssessment.objects.all().values_list('user__email_id', 'date', 'stress_score', 'recommendations')
        for assessment in assessments:
            writer.writerow(assessment)

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-stress-reports/', self.export_as_csv, name="export-stress-reports"),
        ]
        return custom_urls + urls

# Custom admin for Feedback
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'rating', 'date')
    search_fields = ('user__email_id', 'feedback_text')
    list_filter = ('rating', 'date')

# Custom admin for KeyboardActivity
class KeyboardActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'keystrokes_per_minute', 'typing_duration')
    search_fields = ('user__email_id',)
    list_filter = ('timestamp',)

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="keyboard_activity.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Keystrokes/Minute', 'Typing Duration'])
        
        activities = KeyboardActivity.objects.all().values_list('user__email_id', 'timestamp', 'keystrokes_per_minute', 'typing_duration')
        for activity in activities:
            writer.writerow(activity)

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-keyboard-activity/', self.export_as_csv, name="export-keyboard-activity"),
        ]
        return custom_urls + urls

# Custom admin for ScreenTime
class ScreenTimeAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'duration', 'application')
    search_fields = ('user__email_id', 'application')
    list_filter = ('timestamp',)

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="screen_time.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Duration', 'Application'])
        
        screen_times = ScreenTime.objects.all().values_list('user__email_id', 'timestamp', 'duration', 'application')
        for screen_time in screen_times:
            writer.writerow(screen_time)

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-screen-time/', self.export_as_csv, name="export-screen-time"),
        ]
        return custom_urls + urls

# Custom admin for ApplicationUsage
class ApplicationUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'app_name', 'usage_duration')
    search_fields = ('user__email_id', 'app_name')
    list_filter = ('timestamp',)

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="application_usage.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'App Name', 'Usage Duration'])
        
        usages = ApplicationUsage.objects.all().values_list('user__email_id', 'timestamp', 'app_name', 'usage_duration')
        for usage in usages:
            writer.writerow(usage)

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-app-usage/', self.export_as_csv, name="export-app-usage"),
        ]
        return custom_urls + urls

# Custom admin for VoicePattern
class VoicePatternAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'stress_level', 'audio_file_link')
    search_fields = ('user__email_id',)
    list_filter = ('timestamp', 'stress_level')

    def audio_file_link(self, obj):
        if obj.audio_file:
            return format_html('<a href="{}">Download</a>', obj.audio_file.url)
        return "No File"
    audio_file_link.short_description = 'Audio File'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="voice_patterns.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Stress Level', 'Audio File URL'])
        
        patterns = VoicePattern.objects.all().values_list('user__email_id', 'timestamp', 'stress_level', 'audio_file')
        for pattern in patterns:
            audio_url = pattern[3].url if pattern[3] else 'N/A'
            writer.writerow([pattern[0], pattern[1], pattern[2], audio_url])

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-voice-patterns/', self.export_as_csv, name="export-voice-patterns"),
        ]
        return custom_urls + urls

# Custom admin for WearableData
class WearableDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'device_type', 'heart_rate', 'steps', 'sleep_duration', 'stress_indicator')
    search_fields = ('user__email_id', 'device_type')
    list_filter = ('device_type', 'timestamp')

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="wearable_data.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Timestamp', 'Device Type', 'Heart Rate', 'Steps', 'Sleep Duration', 'Stress Indicator'])
        
        data = WearableData.objects.all().values_list(
            'user__email_id', 'timestamp', 'device_type', 'heart_rate', 'steps', 'sleep_duration', 'stress_indicator'
        )
        for entry in data:
            writer.writerow(entry)

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-wearable-data/', self.export_as_csv, name="export-wearable-data"),
        ]
        return custom_urls + urls

# Custom admin for Recommendation
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'recommendation_text', 'priority', 'created_at', 'is_completed')
    search_fields = ('user__email_id', 'recommendation_text', 'category')
    list_filter = ('category', 'priority', 'is_completed', 'created_at')

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recommendations.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Category', 'Recommendation Text', 'Priority', 'Created At', 'Completed'])
        
        recommendations = Recommendation.objects.all().values_list(
            'user__email_id', 'category', 'recommendation_text', 'priority', 'created_at', 'is_completed'
        )
        for recommendation in recommendations:
            writer.writerow(recommendation)

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-recommendations/', self.export_as_csv, name="export-recommendations"),
        ]
        return custom_urls + urls

# Custom admin for Alert
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'threshold', 'triggered_at', 'is_acknowledged')
    search_fields = ('user__email_id', 'message')
    list_filter = ('threshold', 'is_acknowledged', 'triggered_at')

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="alerts.csv"'
        writer = csv.writer(response)
        writer.writerow(['User Email', 'Message', 'Threshold', 'Triggered At', 'Acknowledged'])
        
        alerts = Alert.objects.all().values_list(
            'user__email_id', 'message', 'threshold', 'triggered_at', 'is_acknowledged'
        )
        for alert in alerts:
            writer.writerow(alert)

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-alerts/', self.export_as_csv, name="export-alerts"),
        ]
        return custom_urls + urls

# Custom admin for Resource
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'description_preview', 'url_link', 'file_link')
    search_fields = ('title', 'description', 'category')
    list_filter = ('category',)

    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'

    def url_link(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">Link</a>', obj.url)
        return "No URL"
    url_link.short_description = 'URL'

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file.url)
        return "No File"
    file_link.short_description = 'File'

    def export_as_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="resources.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Category', 'Description', 'URL', 'File URL'])
        
        resources = Resource.objects.all().values_list('title', 'category', 'description', 'url', 'file')
        for resource in resources:
            file_url = resource[4].url if resource[4] else 'N/A'
            writer.writerow([resource[0], resource[1], resource[2], resource[3] or 'N/A', file_url])

        return response

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-resources/', self.export_as_csv, name="export-resources"),
        ]
        return custom_urls + urls

# Register models in the admin panel
admin.site.register(UsersRegister, UsersRegisterAdmin)
admin.site.register(StressAssessment, StressAssessmentAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(KeyboardActivity, KeyboardActivityAdmin)
admin.site.register(ScreenTime, ScreenTimeAdmin)
admin.site.register(ApplicationUsage, ApplicationUsageAdmin)
admin.site.register(VoicePattern, VoicePatternAdmin)
admin.site.register(WearableData, WearableDataAdmin)
admin.site.register(Recommendation, RecommendationAdmin)
admin.site.register(Alert, AlertAdmin)
admin.site.register(Resource, ResourceAdmin)

# Customize admin site header
admin.site.site_header = "Stress Detection Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the Stress Detection Admin Panel"