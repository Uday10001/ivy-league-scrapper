from django.contrib import admin
from django.urls import path
from scraper import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("scrape/", views.trigger_scrape, name="trigger_scrape"),
]
