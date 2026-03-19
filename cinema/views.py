from rest_framework import generics, permissions
from .models import Movie, Room, Seat, Session, Ticket
from .serializers import MovieSerializer, SessionSerializer, SeatMapSerializer, ReservationSerializer
from .services import ReservationService

from rest_framework.views import APIView
from rest_framework.response import Response

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
    
class SeatMapView(generics.ListAPIView):
    serializer_class = SeatMapSerializer

    def get_queryset(self):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        return Seat.objects.filter(room=session.room).order_by('row', 'column')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['session_id'] = self.kwargs.get('session_id')
        return context
    
class SeatDetailView(generics.RetrieveAPIView):
    serializer_class = SeatMapSerializer
    queryset = Seat.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['session_id'] = self.kwargs.get('session_id')
        return context
    
class ReservationSeatView(APIView):
    def post(self, request, session_id, seat_id):
        data = {
            'session_id': session_id,
            'seat_id': seat_id
        }
        serializer = ReservationSerializer(data=data)
        
        if serializer.is_valid():
            session_id = serializer.validated_data['session_id']
            seat_id = serializer.validated_data['seat_id']
            user_id = request.user.id
            sucess = ReservationService.lock_seat(session_id=session_id, seat_id=seat_id, user_id=user_id)

            return Response({"message": "Seat reserved for 10 minutes successfully."}, status=201)
        
        return Response(serializer.errors, status=400)