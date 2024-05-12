from django.urls import path
from .views import create_song
from .views import list_songs
from .views import create_playlist
from .views import list_playlists
from .views import edit_playlist, delete_playlist, list_playlist_songs, move_playlist_song, remove_playlist_song
urlpatterns = [
    path('api/songs/', create_song),
    path('api/available-songs/', list_songs),
    path('api/create-playlist/', create_playlist),
    path('api/list-playlist/', list_playlists),
    path('api/rename-playlist/<int:playlist_id>/', edit_playlist, name = "edit-playlist"),
    path('api/delete-playlist/<int:playlist_id>/', delete_playlist, name = "delete-playlist"),
    path('api/list-playlist-songs/<int:playlist_id>', list_playlist_songs, name = "list-playlist-songs"),
    path('api/move-playlist-songs/<int:playlist_id>/songs/<int:song_id>', move_playlist_song),
    path('api/remove-playlist/<int:playlist_id>/song/<int:song_id>', remove_playlist_song),
]
