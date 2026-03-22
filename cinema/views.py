from rest_framework import generics, permissions
from .models import Movie, Seat, Session, Ticket
from .serializers import MovieSerializer, SessionSerializer, SeatMapSerializer, ReservationSerializer, TicketSerializer, TicketListSerializer
from .services import TicketService

from rest_framework.views import APIView
from rest_framework.response import Response

from django.utils import timezone
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

@extend_schema(auth=[], responses={200: MovieSerializer}, summary="List all movies available", tags=["movies"])
class MovieList(generics.ListAPIView):
    serializer_class = MovieSerializer
    permission_classes=[permissions.AllowAny,]

    def get_queryset(self):
        now = timezone.now()
        return Movie.objects.filter(
            sessions__start_time__gte=now
        ).distinct()
    
@extend_schema(
    auth=[], 
    summary="List all future sessions for a movie",
    responses={
        200: SessionSerializer, 
        404: OpenApiResponse(description="Movie not found")
    },
    tags=["movies"]
)
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

@extend_schema(
    summary="Get seat map for a session",
    responses={
        200: SeatMapSerializer,
        400: OpenApiResponse(description="Bad request"),
        401: OpenApiResponse(description="Unauthorized"),
        404: OpenApiResponse(description="Session not found")
    },
    tags=["seat-map"]
)    
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
    
@extend_schema(
    responses={
        200: SeatMapSerializer,
        400: OpenApiResponse(description="Bad request"),
        401: OpenApiResponse(description="Unauthorized"),
        404: OpenApiResponse(description="Session not found")
    },
    summary="Get a deatailed status of a seat for a session",
    tags=["seat-map"]
)
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

@extend_schema(
    tags=["reservations"]
)
class ReservationSeatView(APIView):
    @extend_schema(
        responses={
            201: OpenApiResponse(description="Seat reserved for 10 minutes successfully"),
            400: OpenApiResponse(description="Bad request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Session or Seat not found")
        },
        summary="Reserve a seat for a session",
    )
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

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Seat reservation cancelled successfully"),
            400: OpenApiResponse(description="Bad request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Session or Seat not found")
        },
        summary="Cancel a reserved seat for a session",
    )    
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
    
@extend_schema(
    summary="Checkout a reserved seat for a session",
    request=None, 
    responses={
        201: TicketSerializer,
        400: OpenApiResponse(description="Bad request"),
        401: OpenApiResponse(description="Unauthorized"),
        404: OpenApiResponse(description="Session or Seat not found")
    },
    tags=["checkout"]
)    
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
    
@extend_schema(
    summary="Get a list of tickets for a user",
    parameters=[
        OpenApiParameter("upcoming", type=bool, required=False)],
    responses={
        200: TicketListSerializer(many=True),
        400: OpenApiResponse(description="Bad request"),
        401: OpenApiResponse(description="Unauthorized")
    },
    tags=["my-tickets"]
)
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