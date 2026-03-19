from django_redis import get_redis_connection
from rest_framework.exceptions import ValidationError

class ReservationService:
    @staticmethod
    def lock_seat(session_id, seat_id, user_id, timeout=600):
        redis_conn = get_redis_connection('default')
        lock_key = f"lock:session:{session_id}:seat:{seat_id}"
        if redis_conn.set(lock_key, user_id, nx=True, ex=timeout):
            return True
        else:
            raise ValidationError(f"Seat {seat_id} is already locked by another user.")