from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        (1, '1 Month'),
        (2, '2 Months'),
        (3, '3 Months'),
        (12, '1 Year'),
    ]
    
    name = models.CharField(max_length=100)
    duration_months = models.IntegerField(choices=DURATION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_duration_months_display()}"

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def clean(self):
        # Ensure time slot is 2 hours
        time_diff = datetime.combine(datetime.today(), self.end_time) - datetime.combine(datetime.today(), self.start_time)
        if time_diff != timedelta(hours=2):
            raise ValidationError("Time slot must be exactly 2 hours")

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=30 * self.plan.duration_months)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.id} - {self.user.username} - {self.payment_status}"

class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ['date', 'time_slot']

    def clean(self):
        if self.user_subscription:
            # Check if the date is a Saturday
            if self.date.weekday() == 5:  # 5 represents Saturday
                raise ValidationError("Gym is closed on Saturdays")
            
            # Check if the appointment is within the subscription period
            if not (self.user_subscription.start_date <= self.date <= self.user_subscription.end_date):
                raise ValidationError("Appointment date must be within subscription period")
            
            # Check if the time slot matches the user's subscription time slot
            if self.time_slot != self.user_subscription.time_slot:
                raise ValidationError("Time slot must match your subscription time slot")

    def __str__(self):
        return f"{self.user.username} - {self.date} {self.time_slot}"

class Exercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category_choices = [
        ('strength', 'Strength'),
        ('cardio', 'Cardio'),
        ('flexibility', 'Flexibility')
    ]
    category = models.CharField(max_length=20, choices=category_choices)
    
    def __str__(self):
        return self.name

class WorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s workout on {self.date}"

class ExerciseLog(models.Model):
    workout_session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.IntegerField()
    reps = models.IntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        if self.exercise.category == 'cardio':
            return f"{self.exercise.name} - {self.duration_minutes} minutes"
        return f"{self.exercise.name} - {self.sets}x{self.reps} @ {self.weight}kg"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    body_fat = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Body fat percentage")
    chest = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Chest measurement in cm")
    waist = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Waist measurement in cm")
    arms = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Arms measurement in cm")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username}'s progress on {self.date}"

class PersonalBest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    reps = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in minutes")
    date_achieved = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'exercise']

    def __str__(self):
        return f"{self.user.username}'s PB for {self.exercise.name}"


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='certificates/')
    issued_date = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Certificate for {self.user.username}"

# Badge Model
class Badge(models.Model):
    BADGE_TYPES = [
        ('Course Completion', 'Course Completion'),
        ('Top Performer', 'Top Performer'),
        ('Consistency Award', 'Consistency Award'),
    ]
    
    POINTS_MAPPING = {
        'Course Completion': 50,
        'Top Performer': 100,
        'Consistency Award': 75,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge_type = models.CharField(max_length=50, choices=BADGE_TYPES)
    awarded_date = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=0)  # New field for points

    def save(self, *args, **kwargs):
        """Assign points based on badge type before saving."""
        if not self.points:  # Assign points only if not already set
            self.points = self.POINTS_MAPPING.get(self.badge_type, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.badge_type} - {self.user.username} ({self.points} pts)"

# Leaderboard Model
class Leaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.points} points"
    

class Contact(models.Model):
    name = models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.CharField(max_length=10)
    desc = models.TextField()

    def __str__(self):
        return self.name