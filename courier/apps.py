# courier/apps.py
from django.apps import AppConfig

class CourierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courier'

    def ready(self):
        import courier.signals
