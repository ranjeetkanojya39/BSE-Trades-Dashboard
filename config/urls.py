from django.urls import path
from trades import views

urlpatterns = [
    path("", views.dashboard),
    path("api/trades", views.api_trades),
    path("api/pull", views.api_pull),
    path("api/status", views.api_status),
    path("api/reset", views.api_reset),
    path("api/stream", views.api_stream),
]
