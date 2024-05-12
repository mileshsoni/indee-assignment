from django.shortcuts import render
import json
from django.http import JsonResponse
from .models import Song
from .serializers import serialize_song, deserialize_song
from django.views.decorators.csrf import csrf_exempt
from .models import Playlist, Song, PlaylistSong
from django.core.paginator import Paginator
@csrf_exempt
def create_song(request):
    if request.method == 'POST':
        song_data = request.body.decode('utf-8')
        song = deserialize_song(song_data)
        song.save()
        return JsonResponse(serialize_song(song), status=201)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
def list_songs(request):
    page_number = int(request.GET.get('page', 1))
    page_size = 10
    search_query = request.GET.get('q', '')
    if search_query:
        songs = Song.objects.filter(name__icontains=search_query).order_by('id')
    else:
        songs = Song.objects.all().order_by('id')
    total_songs = songs.count()
    start_index = (page_number - 1) * page_size
    end_index = min(start_index + page_size, total_songs)
    paginated_songs = songs[start_index:end_index]
    serialized_songs = [serialize_song(song) for song in paginated_songs]
    response_data = {
        'count': total_songs,
        'next': f'/api/songs/?page={page_number + 1}' if end_index < total_songs else None,
        'previous': f'/api/songs/?page={page_number - 1}' if page_number > 1 else None,
        'results': serialized_songs
    }

    return JsonResponse(response_data)

@csrf_exempt
def create_playlist(request):
    body_str = request.body.decode('utf-8')
    data = json.loads(body_str)
    name = data.get('name')
    song_ids = data.get('songs')
    if not name:
        return JsonResponse({'error': 'Name is required'}, status=400)
    playlist = Playlist.objects.create(name=name)
    for position, song_id in enumerate(song_ids, start=1):
        song = Song.objects.get(pk=song_id)
        playlist.songs.add(song, through_defaults={'position': position})
    return JsonResponse({'message': 'Playlist created successfully'}, status=201)

def list_playlists(request):
    page_number = int(request.GET.get('page', 1))
    search_query = request.GET.get('q', '')
    if search_query:
        playlists = Playlist.objects.filter(name__icontains=search_query).order_by('id')
    else:
        playlists = Playlist.objects.all().order_by('id')
    page_size = 10
    total_count = playlists.count()
    total_pages = (total_count + page_size - 1) // page_size
    start_index = (page_number - 1) * page_size
    end_index = min(start_index + page_size, total_count)
    paginated_playlists = playlists[start_index:end_index]
    serialized_playlists = []
    for playlist in paginated_playlists:
        serialized_playlists.append({
            'id': playlist.id,
            'name': playlist.name
        })
    response_data = {
        'count': total_count,
        'next': f'/api/playlists/?page={page_number + 1}' if page_number < total_pages else None,
        'previous': f'/api/playlists/?page={page_number - 1}' if page_number > 1 else None,
        'results': serialized_playlists
    }

    return JsonResponse(response_data)

@csrf_exempt
def edit_playlist(request, playlist_id):
    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        return JsonResponse({'error': 'Playlist not found'}, status=404)

    try:
        data = json.loads(request.body)
        new_name = data.get('name')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format in request body'}, status=400)

    if new_name:
        playlist.name = new_name
        playlist.save()
        return JsonResponse({'message': 'Playlist metadata updated successfully'}, status=200)
    else:
        return JsonResponse({'error': 'Name is required in request body'}, status=400)
    
@csrf_exempt
def delete_playlist(request, playlist_id):
    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        return JsonResponse({'error': 'Playlist not found'}, status=404)
    playlist.delete()
    return JsonResponse({'message': 'Playlist deleted successfully'}, status=200)

def list_playlist_songs(request, playlist_id):
    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        return JsonResponse({'error': 'Playlist not found'}, status=404)
    playlist_songs = PlaylistSong.objects.filter(playlist=playlist).order_by('position')
    page_number = int(request.GET.get('page', 1))
    paginator = Paginator(playlist_songs, 10) 
    paginated_songs = paginator.get_page(page_number)
    serialized_songs = []
    for playlist_song in paginated_songs:
        song = playlist_song.song
        serialized_song = {
            'id': song.id,
            'name': song.name,
            'artist': song.artist,
            'release_year': song.release_year,
            'position': playlist_song.position
        }
        serialized_songs.append(serialized_song)
    response_data = {
        'count': paginator.count,
        'next': paginated_songs.next_page_number() if paginated_songs.has_next() else None,
        'previous': paginated_songs.previous_page_number() if paginated_songs.has_previous() else None,
        'results': serialized_songs
    }

    return JsonResponse(response_data)

@csrf_exempt

def move_playlist_song(request, playlist_id, song_id):
    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        return JsonResponse({'error': 'Playlist not found'}, status=404)
    try:
        playlist_song = PlaylistSong.objects.get(playlist=playlist, song_id=song_id)
    except PlaylistSong.DoesNotExist:
        return JsonResponse({'error': 'Playlist song not found'}, status=404)
    try:
        body = request.body.decode('utf-8')
        body_data = json.loads(body)
        new_position = body_data.get('position')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)
    if new_position is None or not isinstance(new_position, int) or new_position < 1:
        return JsonResponse({'error': 'Invalid position'}, status=400)
    playlist_songs = PlaylistSong.objects.filter(playlist=playlist).order_by('position')
    if new_position < 1 or new_position > len(playlist_songs):
        return JsonResponse({'error': 'Position out of bounds'}, status=400)
    old_position = playlist_song.position
    if new_position < old_position:
        for ps in playlist_songs.filter(position__gte=new_position, position__lt=old_position):
            ps.position += 1
            ps.save()
    elif new_position > old_position:
        for ps in playlist_songs.filter(position__gt=old_position, position__lte=new_position):
            ps.position -= 1
            ps.save()
    playlist_song.position = new_position
    playlist_song.save()
    return JsonResponse({'position': new_position})

@csrf_exempt
def remove_playlist_song(request, playlist_id, song_id):
    try:
        playlist = Playlist.objects.get(pk=playlist_id)
    except Playlist.DoesNotExist:
        return JsonResponse({'error': 'Playlist not found'}, status=404)
    try:
        playlist_song = PlaylistSong.objects.get(playlist=playlist, song_id=song_id)
    except PlaylistSong.DoesNotExist:
        return JsonResponse({'error': 'Playlist song not found'}, status=404)
    position_to_remove = playlist_song.position
    songs_to_shift = PlaylistSong.objects.filter(playlist=playlist, position__gt=position_to_remove)
    for song in songs_to_shift:
        song.position -= 1
        song.save()
    playlist_song.delete()
    return JsonResponse({'message': 'Song has been removed from the playlist'}, status=200)