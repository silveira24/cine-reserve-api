from django.contrib import admin
from .models import Movie, Room, Seat, Session, Ticket
# Register your models here.

admin.site.register(Movie)
admin.site.register(Room)
admin.site.register(Seat)
admin.site.register(Session)
admin.site.register(Ticket)