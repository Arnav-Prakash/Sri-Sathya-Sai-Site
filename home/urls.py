from django.urls import path
from . import views
from .views import SongListView, SongDetailView

urlpatterns = [
    path('', views.index, name="home"),
    path('song/all/', SongListView.as_view(), name="all-songs"),
    path('song/<int:pk>/', SongDetailView.as_view(), name="song-detail"),
    path('song/<int:pk>/review/', views.song_review, name="song-review"),
    #path('fav/<int:id>/', views.favourite_add, name="favourite-add"),
    path('search/', views.search, name="search"),
    path('contact/', views.contact, name="contact"),
]