from django.urls import path
from . import views
from .views import my_certificates, my_badges, leaderboard
from .views import generate_certificate
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('workout/log/', views.workout_log, name='workout_log'),
    path('workout/history/', views.workout_history, name='workout_history'),
    path('progress/track/', views.track_progress, name='track_progress'),
    path('progress/history/', views.progress_history, name='progress_history'),
    path('my-certificates/', my_certificates, name='my_certificates'),
    path('my-badges/', my_badges, name='my_badges'),
    path('leaderboard/', leaderboard, name='leaderboard'),
    path('generate-certificate/<str:username>/', generate_certificate, name='generate_certificate'),
    path('contact/', views.contact, name='contact'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
