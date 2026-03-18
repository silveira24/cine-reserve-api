from rest_framework import generics
from .models import Movie, Room, Seat, Session, Ticket
from .serializers import MovieSerializer

class MovieList(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
