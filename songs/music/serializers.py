import json
from music.models import Song
def serialize_song(song):
    return {
        'name': song.name,
        'artist': song.artist,
        'release_year': song.release_year
    }

def deserialize_song(data):
    data_dict = json.loads(data)
    return Song(
        name=data_dict['name'],
        artist=data_dict['artist'],
        release_year=data_dict['release_year']
    )
