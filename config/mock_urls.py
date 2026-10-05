from django.urls import path
from mock_bse import views

urlpatterns = [
    path("", views.info),
    path("getTrades", views.get_trades),
]
