import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from cinema.models import Movie, Room, Session
from datetime import datetime, timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fixtures_dir = os.path.join(settings.BASE_DIR, 'cinema', 'fixtures')

        rooms_file = os.path.join(fixtures_dir, 'rooms.json')
        with open(rooms_file, 'r') as f:
            rooms_data = json.load(f)
            for item in rooms_data:
                fields = item['fields']
                room, created = Room.objects.get_or_create(
                    name=fields['name'],
                    defaults=fields
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Room {room} created."))


        movies_file = os.path.join(fixtures_dir, 'movies.json')
        with open(movies_file, 'r') as f:
            movies_data = json.load(f)
            movies_to_create = []
            for item in movies_data:
                fields = item['fields']

                if not Movie.objects.filter(title=fields['title']).exists():
                    movies_to_create.append(Movie(**fields))

            if movies_to_create:
                Movie.objects.bulk_create(movies_to_create)
                self.stdout.write(self.style.SUCCESS(f"{len(movies_to_create)} movies created."))

        all_movies = Movie.objects.all()
        all_rooms = Room.objects.all()

        sessions_to_create = []
        now = timezone.now()

        showtimes = ["14:00", "17:00", "21:00"]

        for day_offset in range(8):
            date = now + timedelta(days=day_offset)

            for room in all_rooms:
                for time_str in showtimes:
                    start_dt = timezone.make_aware(
                        datetime.combine(date, datetime.strptime(time_str, "%H:%M").time())
                    )

                    movie = random.choice(all_movies)

                    if not Session.objects.filter(room=room, start_time=start_dt).exists():
                        sessions_to_create.append(
                            Session(
                                movie=movie,
                                room=room,
                                start_time=start_dt
                            )
                        )

        if sessions_to_create:
            Session.objects.bulk_create(sessions_to_create)
            self.stdout.write(self.style.SUCCESS(f"{len(sessions_to_create)} sessions created."))