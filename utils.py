from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from PIL import Image
import io
import time
from datetime import datetime
import mysql.connector
import re

load_dotenv()
LAST_FM_API_KEY = os.getenv('LAST_FM_API_KEY')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
MYSQL_PWD = os.getenv('MYSQL_PWD')

LAST_FM_FIRST_DAY = datetime(2024, 1, 2)
FIRST_DAY_SECONDS = int(LAST_FM_FIRST_DAY.timestamp())

DB = mysql.connector.connect(
    host='localhost',
    user='root',
    password=MYSQL_PWD,
    database='spotify_toolkit'
)
db_cursor = DB.cursor()


def printDict(d):
    for key in d.keys():
        print(f'{key}: {d[key]}')


def spotipySetup():
    scope = 'ugc-image-upload user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public  user-follow-modify user-follow-read user-read-playback-position user-top-read user-read-recently-played user-library-modify user-library-read user-read-email user-read-private'
    load_dotenv()
    return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                                     client_secret=SPOTIFY_CLIENT_SECRET,
                                                     redirect_uri="http://localhost:1234",
                                                     scope=scope))


def update_db(sp):
    def get_bridge_code(title, artist, album):
        return re.sub(r'\W+', '', title + artist + album).lower()

    def remove_apostrophe(str):
        return re.sub("'", '', str).lower()

    db_cursor.execute('SELECT MAX(utc) FROM scrobbles')

    db_max_time = db_cursor.fetchone()[0] + 1

    if not db_max_time:
        db_max_time = FIRST_DAY_SECONDS

    for t in range(db_max_time, int(time.time()), 86400):
        result = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=benfry128&api_key={LAST_FM_API_KEY}&format=json&from={t}&to={t + 86400}&limit=200")
        tracks = result.json()['recenttracks']['track']

        if type(tracks) is dict:
            tracks = [tracks]

        playback = sp.current_playback()
        if playback and playback['is_playing']:
            del tracks[0]  # every lastfm api call returns the currently playing track, so remove if currently playing

        date_str = datetime.fromtimestamp(t).strftime('%m/%d/%Y')
        print(f'Collecting lastfm data around {date_str} ...Got {len(tracks)} tracks')

        for track in tracks:
            utc = int(track['date']['uts']) - 1
            artist = track['artist']['#text']
            album = track['album']['#text']
            title = track['name']

            utc_taken = True
            while utc_taken:
                utc += 1
                db_cursor.execute(f'SELECT utc FROM scrobbles WHERE utc = "{utc}"')
                utc_taken = db_cursor.fetchone()

            bridge_code = get_bridge_code(title, artist, album)

            db_cursor.execute(f'SELECT track_id FROM last_fm_str_tracks WHERE last_fm_str = "{bridge_code}"')
            results = db_cursor.fetchone()

            if results:
                track_id = results[0]
            else:
                uri = None
                possible_tracks = sp.search(q=f'track:{remove_apostrophe(title)} artist:{remove_apostrophe(artist)}', type='track', limit=5)['tracks']['items']
                if possible_tracks:
                    tries = 0
                    for track in possible_tracks:
                        possible_code = get_bridge_code(track['name'], track['artists'][0]['name'], track['album']['name'])
                        if possible_code == bridge_code:
                            if tries:
                                print(f"got it on the {tries + 1}th try")
                            uri = track['uri']
                            title = track['name']
                            artist = track['artists'][0]['name']
                            album = track['album']['name']
                            break
                        tries += 1

                if uri is None:
                    print(f'Any ideas? Track is {title} by {artist} off {album}.')
                    if possible_tracks:
                        print("here are some possible tracks")
                        for track in possible_tracks:
                            print(f"{track['name']} by {track['artists'][0]['name']} off {track['album']['name']}. uri is {track['uri']}")
                    while True:
                        uri = input('\nIf you can find the song, enter the uri. If not, press enter. ')
                        if not uri:
                            break
                        try:
                            track = sp.track(uri)
                        except Exception:
                            print("Yeah that uri didn't work. Try again or press enter to go on")
                            continue
                        else:
                            if input(f"You chose {track['name']} by {track['artists'][0]['name']} off {track['album']['name']} You good with this track?\nPress enter to accept or anything to reject "):
                                print("Ok no go. Try again or press enter to go on")
                                continue
                            else:
                                uri = track['uri']
                                title = track['name']
                                artist = track['artists'][0]['name']
                                album = track['album']['name']
                                break

                if uri:
                    db_cursor.execute(f'SELECT id FROM tracks WHERE spotify_uri = "{uri}"')
                    results = db_cursor.fetchone()
                    if results:
                        track_id = results[0]
                    else:
                        db_cursor.execute('INSERT INTO tracks (name, artist, album, spotify_uri) VALUES (%s, %s, %s, %s)', (title, artist, album, uri))
                        track_id = db_cursor.lastrowid
                else:
                    db_cursor.execute('INSERT INTO tracks (name, artist, album) VALUES (%s, %s, %s)', (title, artist, album))
                    track_id = db_cursor.lastrowid
                db_cursor.execute('INSERT INTO last_fm_str_tracks (last_fm_str, track_id) VALUES (%s, %s)', (bridge_code, track_id))

            db_cursor.execute('INSERT INTO scrobbles (utc, track_id) VALUES (%s, %s)', (utc, track_id))

            print(f'Just added ("{title}", "{artist}", "{album}"), utc was {utc}')
            DB.commit()


def sanitize_db():
    print('checking for duplicates now')

    dupe_checks = ['SELECT utc FROM '
                   '(SELECT utc, track_id, '
                   'LEAD(track_id, 1, 0) OVER (ORDER BY utc) AS idAfter, '
                   'LAG(track_id, 1, 0) OVER (ORDER BY utc) AS idBefore, '
                   'LEAD(utc, 1, 0) OVER (ORDER BY utc) - utc AS timeAfter '
                   'FROM scrobbles ORDER BY utc) t '
                   'WHERE (idBefore = track_id OR idAfter = track_id) AND timeAfter < 60 AND timeAfter > 0;',
                   'SELECT utc FROM '
                   '(SELECT utc, track_id, '
                   'LEAD(track_id, 1, 0) OVER (ORDER BY utc) AS idAfter, '
                   'LAG(track_id, 1, 0) OVER (ORDER BY utc) AS idBefore, '
                   '(LAG(utc, 1, 0) OVER (ORDER BY utc) - utc) * -1 AS timeBefore '
                   'FROM scrobbles ORDER BY utc) t '
                   'WHERE (idBefore = track_id OR idAfter = track_id) AND timeBefore < 60 AND timeBefore > 0;'
                   ]

    for dupe_check in dupe_checks:
        db_cursor.execute(dupe_check)
        dupes = [record[0] for record in db_cursor.fetchall()]
        if dupes:
            if not input(f'About to delete {len(dupes)} records, you good with that?') == '':
                print("SKIPPED")
                continue
            db_cursor.execute(f'DELETE FROM scrobbles WHERE utc in ({str(dupes)[1:-1]})')
            DB.commit()

    # gotta check for dupes in tracks as well
    db_cursor.execute('SELECT name, artist FROM tracks GROUP BY name, artist HAVING COUNT(*) > 1')
    for (track, artist) in db_cursor.fetchall():
        print(f"Ok let's talk about {track} by {artist}")
        db_cursor.execute('SELECT id, album, spotify_uri FROM tracks WHERE name = %s AND artist = %s', (track, artist))
        dupe_records = db_cursor.fetchall()
        for (id, album, uri) in dupe_records:
            print(f"Off of {album}, uri is {uri}")

        keep_id = input("Which one would you like to keep? (0-indexed, press enter to change nothing")
        if keep_id:
            good_track = dupe_records[int(keep_id)][0]
            del dupe_records[int(keep_id)]
            for dupe_record in dupe_records:
                merge_tracks(good_track, dupe_record[0])


def merge_tracks(good_track, bad_track):
    # move all scrobbles from bad to good
    db_cursor.execute(f'UPDATE scrobbles SET track_id = {good_track} WHERE track_id = {bad_track}')
    # move all lastfm str records from bad to good
    db_cursor.execute(f'UPDATE last_fm_str_tracks SET track_id = {good_track} WHERE track_id = {bad_track}')

    db_cursor.execute(f'DELETE FROM tracks WHERE id = {bad_track}')

    DB.commit()


def delete_track(id):
    db_cursor.execute(f'DELETE FROM scrobbles WHERE track_id = {id}')
    db_cursor.execute(f'DELETE FROM last_fm_str_tracks WHERE track_id = {id}')
    db_cursor.execute(f'DELETE FROM tracks WHERE id = {id}')
    DB.commit()


def getRecentTracks(start_days_back, end_days_back, sp):
    update_db(sp)

    sql = 'SELECT utc, name, artist, album FROM scrobbles INNER JOIN tracks ON id = track_id WHERE utc > %s AND utc < %s'
    db_cursor.execute(sql, ((int((time.time()-14400) / 86400) - start_days_back) * 86400 + 14400, (int((time.time()-14400) / 86400) - end_days_back + 1) * 86400 + 14400))
    recents_dicts = [
        {
            'utc': recent[0],
            'name': recent[1],
            'artist': recent[2],
            'album': recent[3]
        } for recent in db_cursor.fetchall()
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
        x = (id % to_a_side) * size
        y = (id // to_a_side) * size
        bigImage.paste(image, (x, y))
        del image
        del response

    bigImage.show()
