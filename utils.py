import io
import mysql.connector
import os
import re
import requests
import spotipy
import time
from dotenv import load_dotenv
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()
LAST_FM_API_KEY = os.getenv('LAST_FM_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
MYSQL_PWD = os.getenv('MYSQL_PWD')


def strip_str(string):
    return re.sub(r'\W+', '', string).lower()


def remove_apostrophe(string):
    return re.sub("'", '', string).lower()


def spotipySetup():
    scope = 'ugc-image-upload user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public  user-follow-modify user-follow-read user-read-playback-position user-top-read user-read-recently-played user-library-modify user-library-read user-read-email user-read-private'
    return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                                     client_secret=SPOTIFY_CLIENT_SECRET,
                                                     redirect_uri="http://localhost:1234",
                                                     scope=scope),
                           requests_timeout=10,
                           retries=1)


def db_setup():
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password=MYSQL_PWD,
        database='spotify_toolkit'
    )
    cursor = db.cursor()
    return (db, cursor)


def merge_tracks(good_track, bad_track, db, cursor):
    cursor.execute('select name, artist from tracks where id in (%s, %s)', (good_track, bad_track))

    [(name1, artist1), (name2, artist2)] = cursor.fetchall()

    if not input(f"About to merge {name1} by {artist1} with {name2} by {artist2}. Good?"):
        # move all scrobbles from bad to good
        cursor.execute(f'UPDATE scrobbles SET track_id = {good_track} WHERE track_id = {bad_track}')
        # move all lastfm str records from bad to good
        cursor.execute(f'UPDATE last_fm_str_tracks SET track_id = {good_track} WHERE track_id = {bad_track}')

        cursor.execute(f'DELETE FROM tracks WHERE id = {bad_track}')

        db.commit()


def delete_track(id, db, cursor):
    cursor.execute(f'DELETE FROM scrobbles WHERE track_id = {id}')
    cursor.execute(f'DELETE FROM last_fm_str_tracks WHERE track_id = {id}')
    cursor.execute(f'DELETE FROM tracks WHERE id = {id}')
    db.commit()


def getRecentTracks(start_days_back, end_days_back, sp, db, cursor):
    sql = 'SELECT utc, name, artist, album FROM scrobbles INNER JOIN tracks ON id = track_id WHERE utc > %s AND utc < %s'
    cursor.execute(sql, ((int((time.time()-14400) / 86400) - start_days_back) * 86400 + 14400, (int((time.time()-14400) / 86400) - end_days_back + 1) * 86400 + 14400))
    recents_dicts = [
        {
            'utc': recent[0],
            'name': recent[1],
            'artist': recent[2],
            'album': recent[3]
        } for recent in cursor.fetchall()
    ]
    return recents_dicts


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

    print(f'Retrieved {len(tracks)}')

    print('Now digging through to find good versions')
    real_tracks = []
    for track in tracks:
        if not track['is_local'] and track['track'] and track['track']['type'] == 'track':
            if 'US' in track['track']['available_markets']:
                real_tracks.append(track['track'])
            else:
                alt = trackDownTrack(track['track'], sp)
                if alt:
                    real_tracks.append(alt)

    print(f'Finished, retrieved {len(real_tracks)} tracks in the end')
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


def compile_image(to_a_side, size, image_urls):
    bigImage = Image.new("RGB", (size * to_a_side, size * to_a_side))

    for id, url in enumerate(image_urls):
        print('Building image...')
        response = requests.get(url, stream=True)
        image = Image.open(io.BytesIO(response.content))
        image.thumbnail((size, size))
        x = (id % to_a_side) * size
        y = (id // to_a_side) * size
        bigImage.paste(image, (x, y))
        del image
        del response

    bigImage.show()


def sp_tracks(sp, cursor):
    cursor.execute("select url from tracks where url like '%spotify%'")

    tracks = [row[0] for row in cursor.fetchall()]
    sp_tracks = []

    for i in range(0, len(tracks), 50):
        sp_tracks.extend(sp.tracks(tracks[i:i+50])['tracks'])
        print(len(sp_tracks))

    return sp_tracks


def sp_albums(sp, cursor):
    cursor.execute("SELECT url FROM albums where url like '%spotify%';")

    albums = [row[0] for row in cursor.fetchall()]
    sp_albums = []

    for i in range(0, len(albums), 20):
        sp_albums.extend(sp.albums(albums[i:i+20])['albums'])
        print(f'{len(sp_albums)} albums loaded from Spotify so far')

    return sp_albums


def album_explicit_and_few_artists(sp_album):
    tracks = sp_album['tracks']['items']
    tracks_explicit = bool([1 for track in tracks if track['explicit']])
    three_or_fewer_artists = len(set([track['artists'][0]['name'] for track in tracks])) <= 3

    return f'{tracks_explicit} and {three_or_fewer_artists}'
