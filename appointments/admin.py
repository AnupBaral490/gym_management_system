from django.contrib import admin
from .models import TimeSlot, Appointment, SubscriptionPlan, UserSubscription
from .models import Certificate, Badge, Leaderboard
from appointments.models import Contact
# Register your models here.

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'is_available')
    list_filter = ('is_available',)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration_months', 'price')
    list_filter = ('duration_months',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'time_slot', 'is_active')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'time_slot', 'status', 'created_at')
    list_filter = ('status', 'date')
    search_fields = ('user__username',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'issued_date')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge_type', 'awarded_date')

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'points')


admin.site.register(Contact)