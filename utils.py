from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests

load_dotenv()
lastFMApiKey = os.getenv('LAST_FM_API_KEY')
spotifyID = os.getenv('SPOTIFY_CLIENT_ID')
spotifySecret = os.getenv('SPOTIFY_CLIENT_SECRET')


def printDict(d):
    for key in d.keys():
        print(f'{key}: {d[key]}')


def spotipySetup(scope):
    load_dotenv()
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotifyID,
                                                   client_secret=spotifySecret,
                                                   redirect_uri="http://localhost:1234",
                                                   scope=scope))
    return sp


def getRecentTracks(startTime, endTime, sp):
    r = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=benfry128&api_key={lastFMApiKey}&format=json&from={startTime}&to={endTime}&limit=200")
    recents = r.json()['recenttracks']['track']

    if type(recents) is dict:
        recents = [recents]

    if sp.current_playback()['is_playing']:
        del recents[0]  # every lastfm api call returns the currently playing track, so remove if currently playing

    print(f'Collecting lastfm data... Got {len(recents)} tracks')

    return recents


def getAllPlaylists(user_id, sp):
    total_playlists = sp.user_playlists(user_id)['total']

    offset = 0
    playlists = []
    while offset < total_playlists:
        playlists.extend(sp.user_playlists(user_id)['items'])
        offset += 50

    return playlists


def getAllTracks(playlist_id, sp):
    print("Getting tracks 0-99")
    result = sp.playlist_tracks(playlist_id)
    total_tracks = result['total']

    offset = 100
    tracks = result['items']
    while offset < total_tracks:
        print(f"Getting tracks {offset}-{offset+99}")
        tracks.extend(sp.playlist_tracks(playlist_id, offset=offset)['items'])
        offset += 100

    real_tracks = []

    for track in tracks:
        if not track['is_local'] and track['track'] and track['track']['type'] == 'track':
            if 'US' in track['track']['available_markets']:
                real_tracks.append(track['track']) 
            else:
                alt = trackDownTrack(track['track'], sp)
                if alt:
                    real_tracks.append(alt)
    print(len(real_tracks))
    return real_tracks


def trackDownTrack(track, sp):
    goodName = track['name'].lower()
    goodArtist = track['artists'][0]['name'].lower()
    isrc = track['external_ids']['isrc']

    good_tracks = sp.search(q=f'isrc:{isrc}', type='track')['tracks']['items']
    if good_tracks:
        return good_tracks[0]

    good_tracks = sp.search(q=f'track:{goodName} artist:{goodArtist}', type='track')['tracks']['items']
    if good_tracks:
        newName = good_tracks[0]['name'].lower()
        newArtist = good_tracks[0]['artists'][0]['name'].lower()

        if goodName == newName and goodArtist == newArtist:
            return good_tracks[0]
    return None
