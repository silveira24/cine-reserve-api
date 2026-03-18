from rest_framework import generics, permissions
from .models import Movie, Room, Seat, Session, Ticket
from .serializers import MovieSerializer, SessionSerializer

from django.utils import timezone
from django.shortcuts import get_object_or_404

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
        movie = get_object_or_404(Movie, id=movie_id)
        return Session.objects.filter(
            movie=movie,
            start_time__gte=timezone.now()
        ).select_related('room').order_by('start_time')