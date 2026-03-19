from rest_framework import generics, permissions
from .models import Movie, Room, Seat, Session, Ticket
from .serializers import MovieSerializer, SessionSerializer, SeatMapSerializer, ReservationSerializer, TicketSerializer, TicketListSerializer
from .services import TicketService

from rest_framework.views import APIView
from rest_framework.response import Response

from django.utils import timezone
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter

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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['session_id'] = self.kwargs.get('session_id')
        return context
    
    def get_queryset(self):
        session_id = self.kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)
        return Seat.objects.filter(room=session.room).order_by('row', 'column')

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
            sucess = TicketService.lock_seat(session_id=session_id, seat_id=seat_id, user_id=user_id)

            return Response({"message": "Seat reserved for 10 minutes successfully."}, status=201)
        
        return Response(serializer.errors, status=400)
    
    def delete(self, request, session_id, seat_id):
        data = {
            'session_id': session_id,
            'seat_id': seat_id
        }
        serializer = ReservationSerializer(data=data)
        
        if serializer.is_valid():
            session_id = serializer.validated_data['session_id']
            seat_id = serializer.validated_data['seat_id']
            user_id = request.user.id
            sucess = TicketService.unlock_seat(session_id=session_id, seat_id=seat_id, user_id=user_id)

            return Response({"message": "Seat reservation cancelled successfully."}, status=204)
        
        return Response(serializer.errors, status=400)
    
@extend_schema(request=None, responses={201: TicketSerializer})    
class CheckoutView(generics.CreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        session_id = kwargs['session_id']
        seat_id = kwargs['seat_id']
        user_id = request.user.id

        data = {
            'session': session_id,
            'seat': seat_id,
            'user': user_id
        }

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)
    
    def perform_create(self, serializer):
        return TicketService.process_checkout(serializer)
    
@extend_schema(parameters=[OpenApiParameter("upcoming", type=bool, required=False)], responses={200: TicketListSerializer(many=True)})
class TicketListView(generics.ListAPIView):
    serializer_class = TicketListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.filter(user=user).select_related('session', 'seat').order_by('-session__start_time')

        upcoming = self.request.query_params.get('upcoming', False)
        if upcoming:
            queryset = queryset.filter(session__start_time__gte=timezone.now())

        return queryset