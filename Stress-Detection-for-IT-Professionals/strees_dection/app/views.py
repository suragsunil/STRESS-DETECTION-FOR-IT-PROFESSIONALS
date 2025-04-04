from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import now, timedelta
from .models import UsersRegister, StressAssessment, Feedback, KeyboardActivity, ScreenTime, ApplicationUsage, VoicePattern, WearableData, Recommendation, Alert, Resource
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import uuid
from .helpers import send_forget_password_mail
import json
import csv
from django.db.models import Avg, Max, Min, Sum
from django.contrib.auth import logout
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    feedbacks = Feedback.objects.select_related('user').order_by('-date')[:3]
    return render(request, 'home.html', {'feedbacks': feedbacks})

def usershome(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            return render(request, 'usershome.html', {'user': user})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in usershome")
            request.session.flush()
            return redirect('login')
    return redirect('login')

def signup(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_id = request.POST.get('email_id')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        image = request.FILES.get('image')
        department = request.POST.get('department')
        new_department = request.POST.get('new_department')
        years_of_experience = request.POST.get('years_of_experience')
        work_role = request.POST.get('work_role')

        if UsersRegister.objects.filter(email_id=email_id).exists():
            messages.error(request, 'Email ID already exists. Please log in.')
            return redirect('/login/')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')

        if department == 'add_new' and new_department:
            department = new_department

        profile = UsersRegister(
            first_name=first_name,
            last_name=last_name,
            email_id=email_id,
            password=password,
            confirm_password=confirm_password,
            image=image,
            department=department,
            years_of_experience=years_of_experience,
            work_role=work_role
        )
        profile.save()

        messages.success(request, 'Signup successful. Please log in.')
        return redirect('/login/')
    return render(request, 'userregistration.html')

def userprofile(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            return render(request, 'userprofile.html', {'user': user})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in userprofile")
            request.session.flush()
            return redirect('login')
    return redirect('login')

def userprofile_edit(request, eid):
    edt = UsersRegister.objects.get(id=eid)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email_id = request.POST.get('email_id')
        password = request.POST.get('password')
        image = request.FILES.get('image')
        department = request.POST.get('department')
        years_of_experience = request.POST.get('years_of_experience')
        work_role = request.POST.get('work_role')

        edt.first_name = first_name
        edt.last_name = last_name
        edt.email_id = email_id
        edt.password = password
        edt.department = department
        edt.years_of_experience = years_of_experience
        edt.work_role = work_role
        if image is not None:
            edt.image = image
        edt.save()
        return redirect("userprofile")
    return render(request, 'edit_profile.html', {'edt': edt})

def get_departments(request):
    departments = UsersRegister.objects.values_list('department', flat=True).distinct()
    return JsonResponse({'departments': list(departments)})

def login(request):
    if request.method == "POST":
        email = request.POST.get('email_id')
        password = request.POST.get('password')
        try:
            user = UsersRegister.objects.get(email_id=email, password=password)
            request.session['email'] = user.email_id
            logger.info(f"User {user.email_id} logged in successfully, session set")
            messages.success(request, 'Login successful.')
            return redirect('/usershome/')
        except UsersRegister.DoesNotExist:
            logger.warning(f"Login failed for email {email}: Invalid credentials")
            msg = "Invalid user"
            return render(request, 'userlogin.html', {"msg": msg})
    return render(request, 'userlogin.html')

def user_logout(request):
    logger.info(f"User {request.session.get('email')} logged out")
    request.session.flush()
    return redirect('home')

def settings_view(request):
    return render(request, 'settings.html')

def faq_view(request):
    return render(request, 'faq.html')

def account_privacy_view(request):
    if 'email' in request.session:
        mail = request.session['email']
        try:
            user = UsersRegister.objects.get(email_id=mail)
            stress_assessments = StressAssessment.objects.filter(user=user).order_by('-date')[:5]
            feedbacks = Feedback.objects.filter(user=user).order_by('-date')[:5]
            return render(request, 'account_privacy.html', {
                'user': user,
                'stress_assessments': stress_assessments,
                'feedbacks': feedbacks
            })
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {mail} not found in account_privacy_view")
            request.session.flush()
            return redirect('login')
    return redirect('login')

def solutions(request):
    return render(request, 'solution.html')

def forget_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = UsersRegister.objects.get(email_id=email)
            token = str(uuid.uuid4())
            user.confirm_password_token = token
            user.save()
            send_forget_password_mail(user.email_id, token)
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('/login/')
        except UsersRegister.DoesNotExist:
            messages.error(request, 'No account found with that email.')
    return render(request, 'forget-password.html')

def change_password(request, token):
    try:
        user = UsersRegister.objects.filter(confirm_password_token=token).first()
        if not user:
            messages.error(request, 'Invalid or expired token.')
            return redirect('/forget-password/')
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect(f'/change-password/{token}/')
            user.password = new_password
            user.confirm_password = new_password
            user.confirm_password_token = None
            user.save()
            messages.success(request, 'Password updated successfully. Please log in.')
            return redirect('/login/')
    except Exception as e:
        logger.error(f"Error in change_password: {str(e)}")
        messages.error(request, 'An error occurred.')
    return render(request, 'change-password.html')

def stress_assessment(request):
    if request.method == "POST":
        responses = request.POST.getlist('responses')
        stress_score = sum(map(int, responses))
        recommendations = "Take a break and practice relaxation techniques." if stress_score > 10 else "You are doing well!"
        email = request.session.get('email')
        user = UsersRegister.objects.get(email_id=email) if email else None
        assessment = StressAssessment.objects.create(
            user=user,
            date=now(),
            responses=json.dumps(responses),
            stress_score=stress_score,
            recommendations=recommendations
        )
        return redirect('stress_result', assessment.id)
    return render(request, "stress_assessment.html")

def stress_result(request, assessment_id):
    assessment = StressAssessment.objects.get(id=assessment_id)
    return render(request, "stress_result.html", {"assessment": assessment})

def dashboard(request):
    email = request.session.get('email')
    if not email:
        return redirect('login')
    try:
        user = UsersRegister.objects.get(email_id=email)
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {email} not found in dashboard")
        request.session.flush()
        return redirect('login')
    assessments = StressAssessment.objects.filter(user=user).order_by('date')
    latest_assessment = assessments.last()
    dates = [assessment.date.strftime("%Y-%m-%d") for assessment in assessments]
    scores = [assessment.stress_score for assessment in assessments]
    total_assessments = assessments.count()
    avg_stress_score = assessments.aggregate(Avg('stress_score'))['stress_score__avg'] or 0
    max_stress_score = assessments.aggregate(Max('stress_score'))['stress_score__max'] or 0
    min_stress_score = assessments.aggregate(Min('stress_score'))['stress_score__min'] or 0
    context = {
        'latest_assessment': latest_assessment,
        'dates': json.dumps(dates),
        'scores': json.dumps(scores),
        'total_assessments': total_assessments,
        'avg_stress_score': avg_stress_score,
        'max_stress_score': max_stress_score,
        'min_stress_score': min_stress_score
    }
    return render(request, 'dashboard.html', context)

def submit_feedback(request, assessment_id):
    if request.method == "POST":
        feedback_text = request.POST.get('feedback_text')
        rating = request.POST.get('rating')
        assessment = get_object_or_404(StressAssessment, id=assessment_id)
        user = UsersRegister.objects.get(email_id=request.session['email'])
        feedback = Feedback(
            user=user,
            assessment=assessment,
            feedback_text=feedback_text,
            rating=rating
        )
        feedback.save()
        messages.success(request, 'Feedback submitted successfully.')
        return redirect('stress_result', assessment_id=assessment_id)
    return render(request, 'submit_feedback.html', {'assessment_id': assessment_id})

def view_feedback(request):
    if 'email' in request.session:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        feedbacks = Feedback.objects.filter(user=user)
        return render(request, 'view_feedback.html', {'feedbacks': feedbacks})
    return redirect('login')

def adminlogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        e = 'admin2024@gmail.com'
        p = 'admin@123'
        if email == e and password == p:
            request.session['email'] = email  # Set session for admin
            return redirect('admin_dashboard')
        else:
            messages.warning(request, 'Incorrect email or password. Please try again.')
    return render(request, 'admin_login.html')

def admin_logout(request):
    logger.info(f"Admin {request.session.get('email')} logged out")
    request.session.flush()
    return redirect('adminlogin')

def admin_manage_users(request):
    users = UsersRegister.objects.all()
    return render(request, "admin_manage_users.html", {"users": users})

def admin_dashboard(request):
    if 'email' not in request.session or request.session['email'] != 'admin2024@gmail.com':
        return redirect('adminlogin')

    users = UsersRegister.objects.all()
    for user in users:
        stress_assessments = StressAssessment.objects.filter(user=user)
        user.stress_trend = stress_assessments.aggregate(Avg('stress_score'))['stress_score__avg'] or 0
        keyboard_data = KeyboardActivity.objects.filter(user=user)
        user.keyboard_review = keyboard_data.aggregate(Sum('keystrokes_per_minute'))['keystrokes_per_minute__sum'] or 0
        feedback_data = Feedback.objects.filter(user=user)
        user.feedback_details = feedback_data.aggregate(Avg('rating'))['rating__avg'] or 0
        voice_data = VoicePattern.objects.filter(user=user)
        user.voice_patterns = voice_data.aggregate(Avg('stress_level'))['stress_level__avg'] or 0
        screen_time_data = ScreenTime.objects.filter(user=user)
        total_seconds = screen_time_data.aggregate(Sum('duration'))['duration__sum'] or 0
        user.screen_time = total_seconds / 3600 if total_seconds else 0

    total_users = users.count()
    assessments = StressAssessment.objects.all().order_by('date')
    total_assessments = assessments.count()
    avg_stress_score = assessments.aggregate(avg_score=Avg('stress_score'))['avg_score'] or 0
    max_stress_score = assessments.aggregate(max_score=Max('stress_score'))['max_score'] or 0
    min_stress_score = assessments.aggregate(min_score=Min('stress_score'))['min_score'] or 0
    dates = [assessment.date.strftime('%Y-%m-%d') for assessment in assessments]
    scores = [assessment.stress_score for assessment in assessments]

    context = {
        'total_users': total_users,
        'avg_stress_score': round(avg_stress_score, 2),
        'max_stress_score': max_stress_score,
        'min_stress_score': min_stress_score,
        'total_assessments': total_assessments,
        'dates': json.dumps(dates),
        'scores': json.dumps(scores),
        'users': users,
    }
    return render(request, 'admin_dashboard.html', context)

def delete_user(request, user_id):
    user = get_object_or_404(UsersRegister, id=user_id)
    user.delete()
    return redirect('admin_manage_users')

def edit_user(request, user_id):
    user = get_object_or_404(UsersRegister, id=user_id)
    if request.method == 'POST':
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.email_id = request.POST['email_id']
        user.department = request.POST['department']
        user.years_of_experience = request.POST['years_of_experience']
        user.work_role = request.POST['work_role']
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password and confirm_password:
            if password == confirm_password:
                user.password = password
                user.confirm_password = confirm_password
            else:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'edit_user.html', {'user': user})
        if 'image' in request.FILES:
            user.image = request.FILES['image']
        user.save()
        messages.success(request, 'User details updated successfully.')
        return redirect('admin_manage_users')
    return render(request, 'edit_user.html', {'user': user})

def export_stress_reports(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stress_reports.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Stress Score', 'Recommendations'])
    assessments = StressAssessment.objects.all().values_list('date', 'stress_score', 'recommendations')
    for assessment in assessments:
        writer.writerow(assessment)
    return response

# Data Collection Views
def data_collection_dashboard(request):
    email = request.session.get('email')
    if not email:
        logger.warning("No email in session, redirecting to login")
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=email)
        logger.info(f"User {user.email_id} accessed data_collection_dashboard")
    except UsersRegister.DoesNotExist:
        logger.error(f"No user found for email: {email}, clearing session and redirecting")
        request.session.flush()
        return redirect('login')
    
    keyboard_data = KeyboardActivity.objects.filter(user=user).order_by('-timestamp')[:5]
    screen_time_data = ScreenTime.objects.filter(user=user).order_by('-timestamp')[:5]
    app_usage_data = ApplicationUsage.objects.filter(user=user).order_by('-timestamp')[:5]
    voice_data = VoicePattern.objects.filter(user=user).order_by('-timestamp')[:5]
    wearable_data = WearableData.objects.filter(user=user).order_by('-timestamp')[:5]
    
    context = {
        'user': user,
        'keyboard_data': keyboard_data,
        'screen_time_data': screen_time_data,
        'app_usage_data': app_usage_data,
        'voice_data': voice_data,
        'wearable_data': wearable_data,
    }
    logger.debug(f"Rendering data_collection_dashboard for user: {user.email_id}")
    return render(request, 'data_collection_dashboard.html', context)

def collect_keyboard_activity(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            keystrokes = int(request.POST.get('keystrokes', 0))
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            KeyboardActivity.objects.create(
                user=user,
                keystrokes_per_minute=keystrokes,
                typing_duration=duration
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_keyboard_activity")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_screen_time(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            application = request.POST.get('application', '')
            
            ScreenTime.objects.create(
                user=user,
                duration=duration,
                application=application
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_screen_time")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_app_usage(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            app_name = request.POST.get('app_name', '')
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            ApplicationUsage.objects.create(
                user=user,
                app_name=app_name,
                usage_duration=duration
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_app_usage")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_voice_pattern(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            audio_file = request.FILES.get('audio_file')
            stress_level = float(request.POST.get('stress_level', 0.0)) if request.POST.get('stress_level') else None
            
            VoicePattern.objects.create(
                user=user,
                audio_file=audio_file,
                stress_level=stress_level
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_voice_pattern")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def collect_wearable_data(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'User not logged in'})
        try:
            user = UsersRegister.objects.get(email_id=email)
            device_type = request.POST.get('device_type')
            heart_rate = int(request.POST.get('heart_rate', 0)) if request.POST.get('heart_rate') else None
            steps = int(request.POST.get('steps', 0)) if request.POST.get('steps') else None
            sleep_duration = timedelta(seconds=int(request.POST.get('sleep_duration', 0))) if request.POST.get('sleep_duration') else None
            stress_indicator = float(request.POST.get('stress_indicator', 0.0)) if request.POST.get('stress_indicator') else None
            
            WearableData.objects.create(
                user=user,
                device_type=device_type,
                heart_rate=heart_rate,
                steps=steps,
                sleep_duration=sleep_duration,
                stress_indicator=stress_indicator
            )
            return JsonResponse({'status': 'success'})
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in collect_wearable_data")
            request.session.flush()
            return JsonResponse({'status': 'error', 'message': 'User not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def post_keyboard_activity(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post keyboard activity.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            keystrokes = int(request.POST.get('keystrokes', 0))
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            KeyboardActivity.objects.create(
                user=user,
                keystrokes_per_minute=keystrokes,
                typing_duration=duration
            )
            messages.success(request, 'Keyboard activity posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_keyboard_activity")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_keyboard_activity.html')

def post_screen_time(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post screen time.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            application = request.POST.get('application', '')
            
            ScreenTime.objects.create(
                user=user,
                duration=duration,
                application=application
            )
            messages.success(request, 'Screen time posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_screen_time")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_screen_time.html')

def post_application_usage(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post application usage.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            app_name = request.POST.get('app_name', '')
            duration = timedelta(seconds=int(request.POST.get('duration', 0)))
            
            ApplicationUsage.objects.create(
                user=user,
                app_name=app_name,
                usage_duration=duration
            )
            messages.success(request, 'Application usage posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_application_usage")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_application_usage.html')

def post_voice_pattern(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post voice pattern.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            audio_file = request.FILES.get('audio_file')
            stress_level = float(request.POST.get('stress_level', 0.0)) if request.POST.get('stress_level') else None
            
            VoicePattern.objects.create(
                user=user,
                audio_file=audio_file,
                stress_level=stress_level
            )
            messages.success(request, 'Voice pattern posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_voice_pattern")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_voice_pattern.html')

def post_wearable_data(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if not email:
            messages.error(request, 'Please log in to post wearable data.')
            return redirect('login')
        try:
            user = UsersRegister.objects.get(email_id=email)
            device_type = request.POST.get('device_type')
            heart_rate = int(request.POST.get('heart_rate', 0)) if request.POST.get('heart_rate') else None
            steps = int(request.POST.get('steps', 0)) if request.POST.get('steps') else None
            sleep_duration = timedelta(seconds=int(request.POST.get('sleep_duration', 0))) if request.POST.get('sleep_duration') else None
            stress_indicator = float(request.POST.get('stress_indicator', 0.0)) if request.POST.get('stress_indicator') else None
            
            WearableData.objects.create(
                user=user,
                device_type=device_type,
                heart_rate=heart_rate,
                steps=steps,
                sleep_duration=sleep_duration,
                stress_indicator=stress_indicator
            )
            messages.success(request, 'Wearable data posted successfully.')
            return redirect('data_collection_dashboard')
        except UsersRegister.DoesNotExist:
            logger.error(f"User with email {email} not found in post_wearable_data")
            request.session.flush()
            return redirect('login')
    return render(request, 'post_wearable_data.html')

# Recommendation, Alert, Resource Views
def recommendation_dashboard(request):
    if 'email' not in request.session:
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        recommendations = Recommendation.objects.filter(user=user, is_completed=False).order_by('-created_at')
        alerts = Alert.objects.filter(user=user, is_acknowledged=False).order_by('-triggered_at')
        resources = Resource.objects.all()[:5]
        
        latest_assessment = StressAssessment.objects.filter(user=user).order_by('-date').first()
        if latest_assessment and not Recommendation.objects.filter(stress_assessment=latest_assessment).exists():
            generate_recommendations(user, latest_assessment)
        
        context = {
            'user': user,
            'recommendations': recommendations,
            'alerts': alerts,
            'resources': resources,
        }
        return render(request, 'recommendation_dashboard.html', context)
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {request.session['email']} not found")
        request.session.flush()
        return redirect('login')

def view_recommendations(request):
    if 'email' not in request.session:
        return redirect('login')
    
    try:
        user = UsersRegister.objects.get(email_id=request.session['email'])
        recommendations = Recommendation.objects.filter(user=user, is_completed=False).order_by('-created_at')
        alerts = Alert.objects.filter(user=user, is_acknowledged=False).order_by('-triggered_at')
        
        latest_assessment = StressAssessment.objects.filter(user=user).order_by('-date').first()
        if latest_assessment and not Recommendation.objects.filter(stress_assessment=latest_assessment).exists():
            generate_recommendations(user, latest_assessment)
        
        context = {
            'user': user,
            'recommendations': recommendations,
            'alerts': alerts,
        }
        return render(request, 'recommendation_view.html', context)
    except UsersRegister.DoesNotExist:
        logger.error(f"User with email {request.session['email']} not found")
        request.session.flush()
        return redirect('login')

def generate_recommendations(user, assessment):
    """Helper function to generate personalized recommendations"""
    stress_score = assessment.stress_score
    
    if stress_score > 20:
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Take a 15-minute break and try deep breathing exercises.",
            category='BREAK',
            priority=3
        )
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Consider a short walk outside to reduce stress.",
            category='EXERCISE',
            priority=2
        )
        Alert.objects.create(
            user=user,
            message="High stress level detected! Please take action.",
            threshold=20
        )
    elif stress_score > 10:
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Try a 5-minute mindfulness meditation.",
            category='MINDFULNESS',
            priority=2
        )
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Review your schedule and prioritize tasks.",
            category='SCHEDULE',
            priority=1
        )
    else:
        Recommendation.objects.create(
            user=user,
            stress_assessment=assessment,
            recommendation_text="Great job! Maintain your well-being with this guided relaxation audio.",
            category='RESOURCE',
            priority=1
        )

def mark_recommendation_complete(request, recommendation_id):
    if request.method == 'POST':
        recommendation = get_object_or_404(Recommendation, id=recommendation_id, user__email_id=request.session.get('email'))
        recommendation.is_completed = True
        recommendation.save()
        messages.success(request, 'Recommendation marked as completed.')
    return redirect('view_recommendations')

def acknowledge_alert(request, alert_id):
    if request.method == 'POST':
        alert = get_object_or_404(Alert, id=alert_id, user__email_id=request.session.get('email'))
        alert.is_acknowledged = True
        alert.save()
        messages.success(request, 'Alert acknowledged.')
    return redirect('view_recommendations')

def view_resources(request):
    resources = Resource.objects.all()
    return render(request, 'resources.html', {'resources': resources})

def admin_manage_recommendations(request):
    recommendations = Recommendation.objects.all().order_by('-created_at')
    return render(request, 'admin_manage_recommendations.html', {'recommendations': recommendations})

def admin_manage_resources(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        url = request.POST.get('url', '')
        file = request.FILES.get('file')
        
        Resource.objects.create(
            title=title,
            description=description,
            category=category,
            url=url if url else None,
            file=file if file else None
        )
        messages.success(request, 'Resource added successfully.')
        return redirect('admin_manage_resources')
    
    resources = Resource.objects.all()
    return render(request, 'admin_manage_resources.html', {'resources': resources})