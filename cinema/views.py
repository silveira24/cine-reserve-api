from rest_framework import generics, permissions
from .models import Movie, Room, Seat, Session, Ticket
from .serializers import MovieSerializer, SessionSerializer

from django.utils import timezone

from drf_spectacular.utils import extend_schema

@extend_schema(auth=[], responses={200: MovieSerializer})
class MovieList(generics.ListAPIView):
    serializer_class = MovieSerializer
    permission_classes=[permissions.AllowAny,]

    def get_queryset(self):
        now = timezone.now()
        return Movie.objects.filter(
            sessions__start_time__gte=now
        ).distinct()
    
@extend_schema(auth=[], responses={200: SessionSerializer})
class MovieSessionList(generics.ListAPIView):
    serializer_class = SessionSerializer
    permission_classes = [permissions.AllowAny,]

    def get_queryset(self):
        movie_id = self.kwargs['movie_id']
        return Session.objects.filter(
            movie__id=movie_id,
            start_time__gte=timezone.now()
        ).select_related('room')