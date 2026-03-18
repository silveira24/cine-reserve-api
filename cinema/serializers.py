from rest_framework import serializers
from .models import Movie, Room, Seat, Session, Ticket

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['title', 'description', 'duration_minutes', 'is_active']