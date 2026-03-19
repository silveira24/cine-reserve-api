from django.contrib import admin
from .models import Movie, Room, Seat, Session, Ticket
# Register your models here.

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'duration_minutes')
    search_fields = ('title',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'rows', 'columns')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'movie', 'room', 'start_time')
    list_filter = ('movie', 'room', 'start_time')

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('id', 'row', 'column', 'room')
    list_filter = ('room',)