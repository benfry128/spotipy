import time
import requests
from utils import album_explicit_and_few_artists, db_setup, LAST_FM_API_KEY, remove_apostrophe, spotipySetup, strip_str
from datetime import datetime

sp = spotipySetup()

(db, cursor) = db_setup()

SEARCH_PRIORITES = [
    lambda track: track['album']['external_urls']['spotify'] in album_urls,
    lambda track: track['explicit'] and track['album']['album_type'] == 'album',
    lambda track: album_explicit_and_few_artists(sp.album(track['album']['uri'])) and track['album']['album_type'] == 'album',
    lambda track: track['explicit'],
    lambda track: album_explicit_and_few_artists(sp.album(track['album']['uri'])),
    lambda _: True,
]


def search_spotify_tracks(sp_tracks, bridge_codes):
    for prio in SEARCH_PRIORITES:
        for sp_track in sp_tracks:
            if prio(sp_track) and (strip_str(sp_track['name'] + sp_track['artists'][0]['name'] + sp_track['album']['name']) in bridge_codes
                                   or not input(f'Is this ok? {sp_track['name']} by {sp_track['artists'][0]['name']} off of {sp_track['album']['name']}')):
                return sp_track
    return None


# save album_urls for checking later
cursor.execute('SELECT url, id FROM albums ORDER BY id')
album_data = cursor.fetchall()
album_urls = [row[0] for row in album_data]
album_ids = [row[1] for row in album_data]

cursor.execute('select url, id from artists order by id')
artist_data = cursor.fetchall()
artist_urls = [row[0] for row in artist_data]
artist_ids = [row[1] for row in artist_data]

# save last_fm_str_tracks for checking later
cursor.execute('SELECT * FROM last_FM_str_tracks;')
last_fm_str_dict = {row[0]: row[1] for row in cursor.fetchall()}

# get max utc in db to determine where to start pulling recents from lastfm
cursor.execute('SELECT MAX(utc) FROM scrobbles')
db_max_time = cursor.fetchone()[0]
start_time = db_max_time + 1 if db_max_time else int(datetime(2024, 1, 2).timestamp())  # if db empty, start on 1/2/2024
last_added_utc = start_time

for seconds in range(start_time, int(time.time()), 43200):
    result = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=benfry128&api_key={LAST_FM_API_KEY}&format=json&from={seconds}&to={seconds + 43200}&limit=200")
    tracks = result.json()['recenttracks']['track']

    if type(tracks) is dict:
        tracks = [tracks]

    date_str = datetime.fromtimestamp(seconds).strftime('%m/%d/%Y')
    print(f'Collecting lastfm data around {date_str} ...Got {len(tracks)} tracks')

    # remove first track if it's a now-playing track
    if tracks and '@attr' in tracks[0] and 'nowplaying' in tracks[0]['@attr'] and tracks[0]['@attr']['nowplaying']:
        del tracks[0]

    # sort tracks by utc to ensure that tracks aren't missed if the script errors out
    sorted_tracks = sorted(tracks, key=(lambda d: int(d['date']['uts'])))

    for track in sorted_tracks:
        utc = int(track['date']['uts'])
        if utc <= last_added_utc:
            utc = last_added_utc + 1

        lfm_artist = track['artist']['#text']
        lfm_album = track['album']['#text']
        lfm_title = track['name']
        print(f'Searching for {lfm_title} by {lfm_artist} off of {lfm_album}.')

        bridge_codes = [strip_str(lfm_title + lfm_artist + lfm_album)]
        remove_comma_from_artist = lfm_artist
        while ', ' in remove_comma_from_artist:
            remove_comma_from_artist = remove_comma_from_artist[0:remove_comma_from_artist.rindex(', ')]
            bridge_codes.append(strip_str(lfm_title + remove_comma_from_artist + lfm_album))

        if bridge_codes[0] in last_fm_str_dict:
            track_id = last_fm_str_dict[bridge_codes[0]]
        else:
            if 'remaster' in lfm_title.lower():
                lfm_title = input("Please input a version of this that removes the 'remastered' part. Thanks! ")

            sp_tracks = sp.search(q=f'track:{remove_apostrophe(lfm_title)} artist:{remove_apostrophe(remove_comma_from_artist)}', type='track', limit=10)['tracks']['items']

            good_track = search_spotify_tracks(sp_tracks, bridge_codes)
            # uncomment this if you Quit out of adding a track because it is bad
            # good_track = False

            if not good_track:
                print(f'Any ideas? Track is {lfm_title} by {lfm_artist} off {lfm_album}. {"\nHere are some possible tracks" if sp_tracks else ""}')
                for sp_track in sp_tracks:
                    print(f"{sp_track['name']} by {sp_track['artists'][0]['name']} off {sp_track['album']['name']}. url is {sp_track['external_urls']['spotify']}")
                url = input('\nIf you can find the song, enter the url. If not, press enter. ')
                if not url:
                    continue  # if they don't enter a url, just skip to next track
                elif url[0:30] == 'https://open.spotify.com/track':
                    good_track = sp.track(url)
                else:
                    corrected_title = input("If the title is wrong, put it in correctly here: ")
                    title = corrected_title if corrected_title else lfm_title
                    corrected_artist = input("If the artist's name is wrong, put it in correctly here: ")
                    artists = [{'name': corrected_artist if corrected_artist else lfm_artist, 'url': input(f'Input URL of artist "{lfm_artist}"')}]
                    additional_artist_name = input("Other artists? Add name here: ")
                    while additional_artist_name:
                        artists.append({'name': additional_artist_name, 'url': input("Give the URL of that artist pls: ")})
                        additional_artist_name = input("Other artists? Add name here: ")
                    runtime = int(input("Runtime? "))
                    album_url = input("Album url? ")
                    album_title = input("Album title? ")
                    album_type = input("Album type? ")

            if good_track:
                title = good_track['name']
                artists = [{'name': artist['name'], 'url': artist['external_urls']['spotify']} for artist in good_track['artists']]
                album_url = good_track['album']['external_urls']['spotify']
                runtime = int(good_track['duration_ms'] / 1000)
                album_title = good_track['album']['name']
                album_type = good_track['album']['album_type']
                url = good_track['external_urls']['spotify']

            cursor.execute(f'SELECT id FROM tracks WHERE url = "{url}"')
            results = cursor.fetchone()
            if results:
                track_id = results[0]
            else:
                input(f'Adding {title} by {artists[0]['name']} off {album_title}. Press Ctrl-C now if this is a mistake')
                if album_url in album_urls:
                    album_id = album_ids[album_urls.index(album_url)]
                else:
                    cursor.execute('INSERT INTO albums (url, name, type) VALUES (%s, %s, %s)', (album_url, album_title, album_type))
                    album_id = cursor.lastrowid
                    album_urls.append(album_url)
                    album_ids.append(album_id)
                cursor.execute('INSERT INTO tracks (name, album_id, url, runtime) VALUES (%s, %s, %s, %s)', (title, album_id, url, runtime))
                track_id = cursor.lastrowid

                primary = 1
                for artist in artists:
                    artist_url = artist['url']
                    if artist_url in artist_urls:
                        artist_id = artist_ids[artist_urls.index(artist_url)]
                    else:
                        cursor.execute('INSERT INTO artists (name, url) VALUES (%s, %s)', (artist['name'], artist_url))
                        artist_id = cursor.lastrowid
                        artist_urls.append(url)
                        artist_ids.append(artist_id)
                    cursor.execute('INSERT INTO tracks_artists (track_id, artist_id, main) VALUES (%s, %s, %s)', (track_id, artist_id, primary))
                    primary = 0

            cursor.execute('INSERT INTO last_fm_str_tracks (last_fm_str, track_id) VALUES (%s, %s)', (bridge_codes[0], track_id))
            last_fm_str_dict[bridge_codes[0]] = track_id

        cursor.execute('INSERT INTO scrobbles (utc, track_id) VALUES (%s, %s)', (utc, track_id))
        last_added_utc = utc

        db.commit()
