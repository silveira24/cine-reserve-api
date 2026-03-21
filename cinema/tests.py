from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient, APITransactionTestCase
from django.db import connections
from accounts.models import User
from cinema.models import Movie, Session, Room, Seat, Ticket

from datetime import datetime, timedelta, time
from django.utils import timezone

from django_redis import get_redis_connection

import threading
class RegisterTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        }

    def test_register_user(self):
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_register_existing_user(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

class AuthTests(APITestCase):
    def setUp(self):
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        User.objects.create_user(**self.user_data)

    def test_user_can_login_and_get_tokens(self):
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }

        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_invalid_credentials(self):
        data = {
            'email': self.user_data['email'],
            'password': 'wrong_password'
        }

        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }

        response = self.client.post(self.login_url, data, format='json')
        refresh_token = response.data['refresh']

        response = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_user_tries_to_acess_protected_route_without_token(self):
        response = self.client.get('/api/sessions/1/seat-map/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_tries_to_acess_protected_route_with_invalid_token(self):
        response = self.client.get('/api/sessions/1/seat-map/', HTTP_AUTHORIZATION='Bearer invalid_token')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class MovieSessionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.movie = Movie.objects.create(title='Test Movie', description='Test Description', duration_minutes=120)
        self.room = Room.objects.create(name='Test Room', rows=10, columns=10)
        start_time = datetime.combine(datetime.now().date() + timedelta(days=1), time(15, 0, 0))
        start_time = timezone.make_aware(start_time)
        self.session = Session.objects.create(
            movie=self.movie,
            room=self.room,
            start_time=start_time
        )

        self.movies_url = reverse('movie-list')
    def test_get_movies(self):
        response = self.client.get(self.movies_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', response.data)), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Movie')

    def test_get_sessions(self):
        sessions_url = reverse('movie-session-list', args=[self.movie.id])
        response = self.client.get(sessions_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', response.data)), 1)

    def test_get_seat_map(self):
        self.client.force_authenticate(user=self.user)
        seat_map_url = reverse('seat-map', args=[self.session.id])
        response = self.client.get(seat_map_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_seat_detail(self):
        self.client.force_authenticate(user=self.user)
        seat = Seat.objects.filter(room=self.room).first()
        seat_detail_url = reverse('seat-detail', args=[self.session.id, seat.id])
        response = self.client.get(seat_detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_seat_detail_wrong_session(self):
        room2 = Room.objects.create(name='Test Room 2', rows=10, columns=10)
        session2 = Session.objects.create(
            movie=self.movie,
            room=room2,
            start_time=timezone.make_aware(datetime.combine(datetime.now().date() + timedelta(days=1), time(15, 0, 0)))
        )
        self.client.force_authenticate(user=self.user)
        seat = Seat.objects.filter(room=self.room).first()
        seat_detail_url = reverse('seat-detail', args=[session2.id + 1, seat.id])
        response = self.client.get(seat_detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class ReservationTests(APITestCase):
    def setUp(self):
        self.redis_conn = get_redis_connection("default")
        self.redis_conn.flushall()
        self.movie = Movie.objects.create(title='Test Movie', description='Test Description', duration_minutes=120)
        self.room = Room.objects.create(name='Test Room', rows=10, columns=10)
        start_time = timezone.make_aware(datetime.combine(datetime.now().date() + timedelta(days=1), time(15, 0, 0)))
        self.session = Session.objects.create(
            movie=self.movie,
            room=self.room,
            start_time=start_time
        )
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.client.force_authenticate(user=self.user)
    def test_reserve_seat(self):
        seat = Seat.objects.filter(room=self.session.room).first()
        reservation_url = reverse('seat-lock', args=[self.session.id, seat.id])
        response = self.client.post(reservation_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        checkout_url = reverse('checkout', args=[self.session.id, seat.id])
        response = self.client.post(checkout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_reserve_reserved_seat(self):
        seat = Seat.objects.filter(room=self.session.room).first()
        user2 = User.objects.create_user(username='testuser2', email='test2@example.com', password='testpassword')
        reservation_url = reverse('seat-lock', args=[self.session.id, seat.id])
        self.client.post(reservation_url, format='json')
        self.client.force_authenticate(user=user2)
        response = self.client.post(reservation_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reserve_purchased_seat(self):
        seat = Seat.objects.filter(room=self.session.room).first()
        user2 = User.objects.create_user(username='testuser2', email='test2@example.com', password='testpassword')
        reservation_url = reverse('seat-lock', args=[self.session.id, seat.id])
        checkout_url = reverse('checkout', args=[self.session.id, seat.id])
        self.client.post(reservation_url, format='json')
        self.client.post(checkout_url, format='json')
        self.client.force_authenticate(user=user2)
        response = self.client.post(reservation_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class ConcurrencyTests(APITransactionTestCase):
    def setUp(self):
        self.redis_conn = get_redis_connection("default")
        self.redis_conn.flushall()
        self.movie = Movie.objects.create(title='Test Movie', description='Test Description', duration_minutes=120)
        self.room = Room.objects.create(name='Test Room', rows=10, columns=10)
        start_time = timezone.make_aware(datetime.combine(datetime.now().date() + timedelta(days=1), time(15, 0, 0)))
        self.session = Session.objects.create(
            movie=self.movie,
            room=self.room,
            start_time=start_time
        )
        self.seat = Seat.objects.filter(room=self.session.room).first()
        self.url = reverse('seat-lock', args=[self.session.id, self.seat.id])
        self.user1 = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.user2 = User.objects.create_user(username='testuser2', email='test2@example.com', password='testpassword')
        self.results = []

    def make_reservation(self, user):
        try:
            client = APIClient()
            client.force_authenticate(user=user)
            response = client.post(self.url, format='json')
            self.results.append(response.status_code)
        finally:
            for conn in connections.all():
                conn.close()

    def test_simultaneous_reservations(self):
        thread1 = threading.Thread(target=self.make_reservation, args=(self.user1,))
        thread2 = threading.Thread(target=self.make_reservation, args=(self.user2,))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        self.assertEqual(self.results.count(201), 1)
        self.assertEqual(self.results.count(400), 1)

class TicketsTests(APITestCase):
    def setUp(self):
        self.movie = Movie.objects.create(title='Test Movie', description='Test Description', duration_minutes=120)
        self.room = Room.objects.create(name='Test Room', rows=10, columns=10)
        future_time = timezone.make_aware(datetime.combine(datetime.now().date() + timedelta(days=1), time(15, 0, 0)))
        past_time = timezone.make_aware(datetime.combine(datetime.now().date() - timedelta(days=1), time(15, 0, 0)))
        self.session_future = Session.objects.create(
            movie=self.movie,
            room=self.room,
            start_time=future_time
        )
        self.session_past = Session.objects.create(
            movie=self.movie,
            room=self.room,
            start_time=past_time
        )
        self.seat = Seat.objects.filter(room=self.room).first()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.ticket1 = Ticket.objects.create(
            session=self.session_past,
            seat=self.seat,
            user=self.user
        )
        self.ticket2 = Ticket.objects.create(
            session=self.session_future,
            seat=self.seat,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)
    def test_get_all_tickets(self):
        url = reverse('ticket-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_get_upcoming_tickets(self):
        url = reverse('ticket-list') + '?upcoming=true'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)