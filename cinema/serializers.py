from rest_framework import serializers
from .models import Movie, Room, Seat, Session, Ticket

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'duration_minutes']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'movie', 'room', 'start_time']