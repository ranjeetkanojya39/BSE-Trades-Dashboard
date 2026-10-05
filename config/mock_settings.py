"""Mock BSE server ke liye settings: python manage.py runserver 8001 --settings=config.mock_settings"""
from .settings import *  # noqa

ROOT_URLCONF = "config.mock_urls"
AUTO_PULL_ON_START = False
