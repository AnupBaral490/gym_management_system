from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from .models import Appointment, TimeSlot, SubscriptionPlan, UserSubscription, Payment, WorkoutSession, Exercise, ExerciseLog, UserProgress, PersonalBest
from datetime import datetime, timedelta
from django.utils import timezone
import uuid
from .models import Certificate, Badge, Leaderboard
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Certificate, Badge, Leaderboard
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.contrib.auth import login, logout, authenticate
from appointments.models import Contact
def user_login(request):
    if request.method == "POST":
        user = authenticate(username=request.POST["username"], password=request.POST["password"])
        if user:
            login(request, user)  # Creates session
            return redirect("dashboard")
        else:
            return HttpResponse("Invalid credentials")
        


def user_logout(request):
    logout(request)  # Clears session
    return redirect("login")


# View My Certificates
@login_required
def my_certificates(request):
    certificates = Certificate.objects.filter(user=request.user)
    return render(request, 'appointments/my_certificates.html', {'certificates': certificates})

# View My Badges
@login_required
def my_badges(request):
    badges = Badge.objects.filter(user=request.user)
    return render(request, 'appointments/my_badges.html', {'badges': badges})

# View Leaderboard
def leaderboard(request):
    leaderboard_data = User.objects.annotate(total_points=Sum('badge__points')).order_by('-total_points')

    user_rank = None
    for index, user in enumerate(leaderboard_data, start=1):
        if user == request.user:
            user_rank = index
            break

    return render(request, 'appointments/leaderboard.html', {
        'leaderboard': leaderboard_data,
        'current_user': request.user,
        'user_rank': user_rank
        })
    #leaderboard_data = Leaderboard.objects.order_by('-points')
    #return render(request, 'appointments/leaderboard.html', {'leaderboard': leaderboard_data})
# Create your views here.

def home(request):
    context = {
        'subscription_plans': SubscriptionPlan.objects.all()
    }
    if request.user.is_authenticated:
        context['user_subscription'] = UserSubscription.objects.filter(
            user=request.user,
            is_active=True,
            end_date__gte=timezone.now().date()
        ).first()
    return render(request, 'appointments/home.html', context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'appointments/register.html', {'form': form})

@login_required
def subscribe(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    time_slots = TimeSlot.objects.all()

    if request.method == 'POST':
        time_slot_id = request.POST.get('time_slot')
        if not time_slot_id:
            messages.error(request, 'Please select a time slot')
            return redirect('subscribe', plan_id=plan_id)

        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            subscription_plan=plan,
            amount=plan.price,
            payment_status='completed'  # Mark as completed for now
        )

        # Create user subscription
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id)
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=30 * plan.duration_months)
        
        UserSubscription.objects.create(
            user=request.user,
            plan=plan,  
            time_slot=time_slot,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )

        messages.success(request, f'Successfully subscribed to {plan.name}!')
        return redirect('my_appointments')

    return render(request, 'appointments/subscribe.html', {
        'plan': plan,
        'time_slots': time_slots
    })

@login_required
def book_appointment(request):
    # Check if user has active subscription
    subscription = UserSubscription.objects.filter(
        user=request.user,
        is_active=True,
        end_date__gte=timezone.now().date()
    ).first()
    
    if not subscription:
        messages.error(request, 'You need an active subscription to book appointments.')
        return redirect('home')
    
    if request.method == 'POST':
        date = request.POST.get('date')
        
        try:
            # Use the time slot from subscription
            appointment = Appointment.objects.create(
                user=request.user,
                user_subscription=subscription,
                date=date,
                time_slot=subscription.time_slot,
                status='pending'
            )
            messages.success(request, 'Appointment booked successfully!')
            return redirect('my_appointments')
        except Exception as e:
            messages.error(request, str(e))
    
    return render(request, 'appointments/book.html', {
        'subscription': subscription
    })

@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(
        user=request.user
    ).select_related('time_slot', 'user_subscription').order_by('date', 'time_slot__start_time')
    
    return render(request, 'appointments/my_appointments.html', {
        'appointments': appointments
    })

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
    
    if appointment.status != 'cancelled':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'Appointment is already cancelled.')
    
    return redirect('my_appointments')

@login_required
def workout_log(request):
    if request.method == 'POST':
        # Create a new workout session
        appointment_id = request.POST.get('appointment')
        appointment = None
        if appointment_id:
            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
        
        session = WorkoutSession.objects.create(
            user=request.user,
            notes=request.POST.get('notes', ''),
            appointment=appointment
        )
        
        # Process exercise logs
        exercises = request.POST.getlist('exercise')
        sets = request.POST.getlist('sets')
        reps = request.POST.getlist('reps')
        weights = request.POST.getlist('weight')
        durations = request.POST.getlist('duration')
        
        for i in range(len(exercises)):
            exercise = get_object_or_404(Exercise, id=exercises[i])
            ExerciseLog.objects.create(
                workout_session=session,
                exercise=exercise,
                sets=sets[i] if sets[i] else 0,
                reps=reps[i] if reps[i] else 0,
                weight=weights[i] if weights[i] else None,
                duration_minutes=durations[i] if durations[i] else None
            )
        
        messages.success(request, 'Workout logged successfully!')
        return redirect('workout_history')
    
    exercises = Exercise.objects.all()
    today_appointment = Appointment.objects.filter(
        user=request.user,
        date=timezone.now().date(),
        status='confirmed'
    ).first()
    
    return render(request, 'appointments/workout_log.html', {
        'exercises': exercises,
        'today_appointment': today_appointment
    })

@login_required
def workout_history(request):
    sessions = WorkoutSession.objects.filter(user=request.user).order_by('-date')
    return render(request, 'appointments/workout_history.html', {'sessions': sessions})

@login_required
def track_progress(request):
    if request.method == 'POST':
        UserProgress.objects.create(
            user=request.user,
            weight=request.POST.get('weight'),
            body_fat=request.POST.get('body_fat') or None,
            chest=request.POST.get('chest') or None,
            waist=request.POST.get('waist') or None,
            arms=request.POST.get('arms') or None,
            notes=request.POST.get('notes', '')
        )
        messages.success(request, 'Progress tracked successfully!')
        return redirect('progress_history')
    
    return render(request, 'appointments/track_progress.html')

@login_required
def progress_history(request):
    progress_entries = UserProgress.objects.filter(user=request.user)
    personal_bests = PersonalBest.objects.filter(user=request.user).select_related('exercise')
    
    # Calculate progress metrics
    if len(progress_entries) >= 2:
        latest = progress_entries[0]
        oldest = progress_entries.last()
        weight_change = latest.weight - oldest.weight
        
        if latest.body_fat and oldest.body_fat:
            fat_change = latest.body_fat - oldest.body_fat
        else:
            fat_change = None
    else:
        weight_change = None
        fat_change = None
    
    # Get exercise progress
    exercise_progress = {}
    for log in ExerciseLog.objects.filter(
        workout_session__user=request.user
    ).select_related('exercise'):
        if log.exercise.category == 'strength' and log.weight:
            if log.exercise.id not in exercise_progress:
                exercise_progress[log.exercise.id] = {
                    'name': log.exercise.name,
                    'weights': []
                }
            exercise_progress[log.exercise.id]['weights'].append(log.weight)
    
    # Update personal bests
    for log in ExerciseLog.objects.filter(workout_session__user=request.user):
        pb, created = PersonalBest.objects.get_or_create(
            user=request.user,
            exercise=log.exercise,
            defaults={
                'weight': log.weight,
                'reps': log.reps,
                'duration': log.duration_minutes
            }
        )
        
        if not created:
            if log.exercise.category == 'strength' and log.weight:
                if not pb.weight or log.weight > pb.weight:
                    pb.weight = log.weight
                    pb.reps = log.reps
                    pb.save()
            elif log.exercise.category == 'cardio' and log.duration_minutes:
                if not pb.duration or log.duration_minutes > pb.duration:
                    pb.duration = log.duration_minutes
                    pb.save()
    
    context = {
        'progress_entries': progress_entries,
        'personal_bests': personal_bests,
        'weight_change': weight_change,
        'fat_change': fat_change,
        'exercise_progress': exercise_progress.values()
    }
    return render(request, 'appointments/progress_history.html', context)


def generate_certificate(request, username):
    user = get_object_or_404(User, username=username)
    certificate_name = f"certificate_{user.username}.pdf"
    
    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{certificate_name}"'

    # Generate PDF content
    p = canvas.Canvas(response, pagesize=letter)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(200, 750, "Fitness Certification")
    p.setFont("Helvetica", 18)
    p.drawString(220, 700, f"Awarded to: {user.first_name} {user.last_name}")
    p.drawString(220, 670, "For completing the fitness course successfully")
    p.setFont("Helvetica", 12)
    p.drawString(220, 640, f"Date: {user.date_joined.strftime('%Y-%m-%d')}")
    p.showPage()
    p.save()

    # Save certificate in the database
    Certificate.objects.create(user=user, file=certificate_name)

    # Award Badge for Course Completion
    Badge.objects.create(user=user, badge_type='Course Completion')

    # Update Leaderboard
    leaderboard_entry, created = Leaderboard.objects.get_or_create(user=user)
    leaderboard_entry.points += 10  # Example: Add 10 points for course completion
    leaderboard_entry.save()

    # Email certificate
    email = EmailMessage(
        "Your Fitness Certificate",
        "Congratulations! Please find your certificate attached.",
        "admin@fitnesscenter.com",
        [user.email]
    )
    email.attach(certificate_name, response.getvalue(), 'application/pdf')
    email.send()

    return response


@login_required
def dashboard(request):
    user_appointments = Appointment.objects.filter(user=request.user)  # Only show current user’s appointments
    return render(request, "dashboard.html", {"appointments": user_appointments})

def contact(request): 
    if request.method=="POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        desc = request.POST['desc']
        #print(name, email, phone, desc)

        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        print("The data has been written to the db")
    #return HttpResponse("This is my homepage(/contact)")
    return render(request, 'appointments/contact.html')
