import sys
import threading

from django.apps import AppConfig
from django.conf import settings


class TradesConfig(AppConfig):
    name = "trades"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Server start hone par ek baar pull trigger (scheduler nahi, sirf startup trigger).
        # runserver ko --noreload ke saath chalao warna do baar start hoga.
        if settings.AUTO_PULL_ON_START and "runserver" in sys.argv:
            from . import services
            threading.Timer(3, services.start_pull).start()
