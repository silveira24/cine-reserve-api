from django.db import models

from accounts.models import User

class Movie(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Room(models.Model):
    name = models.CharField(max_length=20)
    rows = models.PositiveIntegerField()
    columns = models.PositiveIntegerField()

    def __str__(self):
        return self.name
    
class Session(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.DateTimeField()

    def __str__(self):
        return f"{self.movie} - {self.room} - {self.start_time}"
    
class Seat(models.Model):
    Room = models.ForeignKey(Room, on_delete=models.CASCADE)
    row = models.PositiveIntegerField()
    column = models.PositiveIntegerField()

    def __str__(self):
        return f"Row {self.row}, Column {self.column}"
    
class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.session} - {self.seat}"