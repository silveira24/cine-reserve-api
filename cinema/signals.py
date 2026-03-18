from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Room, Seat

@receiver(post_save, sender=Room)
def create_seats_for_new_room(sender, instance, created, **kwargs):
    '''
    Create automatically seats for a new room.
    '''
    if created:
        seats = []
        for row in range(1, instance.rows + 1):
            for column in range(1, instance.columns + 1):
                seats.append(Seat(room=instance, row=chr(64 + row), column=column))

        Seat.objects.bulk_create(seats)