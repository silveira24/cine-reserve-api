from django.urls import path
from .views import MovieList, MovieSessionList

urlpatterns = [
    path('movies/', MovieList.as_view(), name='movie-list'),
    path('movies/<int:movie_id>/sessions/', MovieSessionList.as_view(), name='movie-session-list'),
]