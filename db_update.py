import time
import requests
from utils import album_explicit, db_setup, LAST_FM_API_KEY, remove_apostrophe, spotipySetup, strip_str
from datetime import datetime

sp = spotipySetup()

(db, cursor) = db_setup()

# save album_urls for checking later
cursor.execute('SELECT url FROM albums')
album_urls = [row[0] for row in cursor.fetchall()]

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
    if '@attr' in tracks[0] and 'nowplaying' in tracks[0]['@attr'] and tracks[0]['@attr']['nowplaying']:
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

        if 'remaster' in lfm_title.lower():
            print(f"Ok the current name for this track is {lfm_title}")
            lfm_title = input("Please input a version of this that removes the 'remastered' part. Thanks! ")

        bridge_code = strip_str(lfm_title + lfm_artist + lfm_album)

        if bridge_code in last_fm_str_dict:
            track_id = last_fm_str_dict[bridge_code]
        else:
            url = None
            possible_tracks = sp.search(q=f'track:{remove_apostrophe(lfm_title)} artist:{remove_apostrophe(lfm_artist)}', type='track', limit=10)['tracks']['items']

            for track in possible_tracks:  # @TODO: just delete tracks from the list that don't work and then let the person choose
                
                
                
                if (shorter_bridge_code == strip_str(track['name'] + track['artists'][0]['name'])
                    and (strip_str(track['name'] + track['artists'][0]['name'])
                         or input(f'Is it ok to substitute {track['album']['name']} for {lfm_album}'))):
                    if not url or track['explicit'] or track['external_urls']['spotify'] in album_urls or album_explicit(sp.album(track['album']['external_urls']['spotify'])):
                        url = track['external_urls']['spotify']
                        title = track['name']
                        artist = track['artists'][0]['name']
                        album_url = track['album']['external_urls']['spotify']
                        runtime = int(track['duration_ms'] / 1000)
                        album_title = track['album']['name']
                        album_type = track['album']['album_type']
                        print(url)
                        if album_url in album_urls:
                            print("ok we're done here")
                            break

            if not url:
                print(f'Any ideas? Track is {lfm_title} by {lfm_artist} off {lfm_album}. {"\nHere are some possible tracks" if possible_tracks else ""}')
                for track in possible_tracks:
                    print(f"{track['name']} by {track['artists'][0]['name']} off {track['album']['name']}. url is {track['external_urls']['spotify']}")
                    if track['external_urls']['spotify'] in album_urls:
                        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~^PAY ATTENTION HERE, THIS ALBUM IS IN THE DB^~~~~~~~~~~~~~~~~")
                while True:
                    url = input('\nIf you can find the song, enter the url. If not, press enter. ')
                    if not url:
                        break
                    if url[0:30] == 'https://open.spotify.com/track':
                        track = sp.track(url)
                        if input(f"You chose {track['name']} by {track['artists'][0]['name']} off {track['album']['name']} You good with this track?\nPress enter to accept or anything to reject "):
                            print("Ok no go. Try again or press enter to go on")
                            continue
                        else:
                            title = track['name']
                            artist = track['artists'][0]['name']
                            album_url = track['album']['external_urls']['spotify']
                            runtime = int(track['duration_ms'] / 1000)
                            album_title = track['album']['name']
                            album_type = track['album']['album_type']
                            break
                    else:
                        title = lfm_title
                        artist = lfm_artist
                        runtime = int(input("Runtime? "))
                        album_url = input("Album url? ")
                        album_title = input("Album title? ")
                        album_type = input("Album type? ")

            if not url:
                continue  # if they don't enter a url, just skip to next track

            cursor.execute(f'SELECT id FROM tracks WHERE url = "{url}"')
            results = cursor.fetchone()
            if results:
                track_id = results[0]
            else:
                if album_url not in album_urls:
                    cursor.execute('INSERT INTO albums (url, title, type) VALUES (%s, %s, %s)', (album_url, album_title, album_type))
                    album_urls.append(album_url)
                cursor.execute('INSERT INTO tracks (name, artist, album, url, runtime) VALUES (%s, %s, %s, %s, %s)', (title, artist, album_url, url, runtime))
                track_id = cursor.lastrowid

            cursor.execute('INSERT INTO last_fm_str_tracks (last_fm_str, track_id) VALUES (%s, %s)', (bridge_code, track_id))

        cursor.execute('INSERT INTO scrobbles (utc, track_id) VALUES (%s, %s)', (utc, track_id))
        last_added_utc = utc

        print(f'Just added ("{lfm_title}", "{lfm_artist}", "{lfm_album}"), utc was {utc}')
        db.commit()
