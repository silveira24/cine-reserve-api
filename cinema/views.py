from rest_framework import generics
from .models import Movie, Room, Seat, Session, Ticket
from .serializers import MovieSerializer

from django.utils import timezone

class MovieList(generics.ListAPIView):
    serializer_class = MovieSerializer

    def get_queryset(self):
        now = timezone.now()
        return Movie.objects.filter(
            sessions__start_time__gte=now
        ).distinct()