import os
import django
from datetime import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_appointment.settings')
django.setup()

from appointments.models import TimeSlot

# Create time slots if they don't exist
time_slots = [
    ('06:00', '07:00'),
    ('07:00', '08:00'),
    ('08:00', '09:00'),
    ('09:00', '10:00'),
    ('16:00', '17:00'),
    ('17:00', '18:00'),
    ('18:00', '19:00'),
    ('19:00', '20:00'),
]

for start, end in time_slots:
    TimeSlot.objects.get_or_create(
        start_time=time.fromisoformat(start),
        end_time=time.fromisoformat(end),
        defaults={'is_available': True}
    )
