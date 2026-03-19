from django_redis import get_redis_connection
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import Ticket

class TicketService:
    @staticmethod
    def lock_seat(session_id, seat_id, user_id, timeout=600):
        redis_conn = get_redis_connection('default')
        lock_key = f"lock:session:{session_id}:seat:{seat_id}"
        if Ticket.objects.filter(session_id=session_id, seat_id=seat_id).exists():
            raise ValidationError(f"Seat {seat_id} is already purchased.")
        if redis_conn.set(lock_key, user_id, nx=True, ex=timeout):
            return True
        else:
            raise ValidationError(f"Seat {seat_id} is already reserved.")
        
    @staticmethod
    def unlock_seat(session_id, seat_id, user_id):
        redis_conn = get_redis_connection('default')
        lock_key = f"lock:session:{session_id}:seat:{seat_id}"
        lock_owner = redis_conn.get(lock_key)
        if not lock_owner:
            raise ValidationError(f"Seat {seat_id} is not reserved.")
        if int(lock_owner) != user_id:
            raise ValidationError(f"Seat {seat_id} is reserved by another user.")
        redis_conn.delete(lock_key)
        
    @staticmethod
    def process_checkout(serializer):
        session = serializer.validated_data['session']
        seat = serializer.validated_data['seat']
        user = serializer.validated_data['user']

        redis_conn = get_redis_connection('default')
        lock_key = f"lock:session:{session.id}:seat:{seat.id}"

        lock_owner = redis_conn.get(lock_key)

        if not lock_owner:
            raise ValidationError(f"Seat {seat.id} is not reserved.")
        
        if lock_owner and int(lock_owner) != user.id:
            raise ValidationError(f"Seat {seat.id} is already reserved by another user.")

        try:
            with transaction.atomic():
                ticket = serializer.save()

                redis_conn.delete(lock_key)

                return ticket
        except Exception as e:
            raise ValidationError(f"Error processing checkout: {str(e)}")