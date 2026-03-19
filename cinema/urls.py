from django.urls import path
from .views import MovieList, MovieSessionList, SeatMapView, SeatDetailView, ReservationSeatView, CheckoutView, TicketListView

urlpatterns = [
    path('movies/', MovieList.as_view(), name='movie-list'),
    path('movies/<int:movie_id>/sessions/', MovieSessionList.as_view(), name='movie-session-list'),
    path('sessions/<int:session_id>/seat-map/', SeatMapView.as_view(), name='seat-map'),
    path('sessions/<int:session_id>/seat-map/<int:pk>/', SeatDetailView.as_view(), name='seat-detail'),
    path('sessions/<int:session_id>/reserve/<int:seat_id>', ReservationSeatView.as_view(), name='seat-lock'),
    path('sessions/<int:session_id>/checkout/<int:seat_id>', CheckoutView.as_view(), name='checkout'),
    path('my-tickets/', TicketListView.as_view(), name='ticket-list'),
]