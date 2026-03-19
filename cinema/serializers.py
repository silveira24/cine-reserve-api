from rest_framework import serializers
from .models import Movie, Room, Seat, Session, Ticket
from django_redis import get_redis_connection

from django.utils import timezone

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'description', 'duration_minutes']

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ['id', 'movie', 'room', 'start_time']

class SeatMapSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Seat
        fields = ['id', 'row', 'column', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = self.context.get('session_id')
        print(f"Debug: session_id: {self.session_id}")
        self.purchased_ids = set()
        self.locked_ids = set()

        if self.session_id:
            self.purchased_ids = set(
                Ticket.objects.filter(session_id=self.session_id)
                .values_list('seat_id', flat=True)
            )

            redis_conn = get_redis_connection('default')
            self.locked_seats = redis_conn.keys(f"lock:session:{self.session_id}:seat:*")
            self.locked_ids = {int(seat.decode('utf-8').split(':')[-1]) for seat in self.locked_seats}

    def get_status(self, obj):

        if obj.id in self.purchased_ids:
            return 'Purchased'

        if obj.id in self.locked_ids:
            return 'Reserved'

        return 'Available'
    
class ReservationSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    seat_id = serializers.IntegerField()

    def validate(self, data):
        session = Session.objects.get(id=data['session_id'])
        seat = Seat.objects.get(id=data['seat_id'])
        if not session:
            raise serializers.ValidationError("Session does not exist.")
        if not session.start_time > timezone.now():
            raise serializers.ValidationError("Session start time has passed.")
        if not seat:
            raise serializers.ValidationError("Seat does not exist.")
        if not seat.room == session.room:
            raise serializers.ValidationError("Seat is not in the same room as the session.")
        return data
