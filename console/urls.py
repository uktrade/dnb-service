from django.urls import path

from .views import SearchView, DetailView

app_name = 'console'

urlpatterns = [
    path('', SearchView.as_view(), name='search'),
    path('detail/<int:duns>/', DetailView.as_view(), name='detail'),
]
