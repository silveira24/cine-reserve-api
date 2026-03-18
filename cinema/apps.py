from django.apps import AppConfig


class CinemaConfig(AppConfig):
    name = 'cinema'

    def ready(self):
        import cinema.signals