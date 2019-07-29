from django.urls import path

from .views import SearchView

app_name = 'console'

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
]
