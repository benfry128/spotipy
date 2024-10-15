import time
import requests
from utils import album_explicit_and_few_artists, db_setup, iso_to_seconds, LAST_FM_API_KEY, remove_apostrophe, spotipy_setup, strip_str, YOUTUBE_API_KEY
from datetime import datetime

sp = spotipy_setup()

(db, cursor) = db_setup()

SEARCH_PRIORITES = [
    lambda track: 'sp' + track['album']['id'] in album_uri_matches,
    lambda track: track['explicit'] and track['album']['album_type'] == 'album',
    lambda track: album_explicit_and_few_artists(sp.album(track['album']['id'])) and track['album']['album_type'] == 'album',
    lambda track: track['explicit'],
    lambda track: album_explicit_and_few_artists(sp.album(track['album']['id'])),
    lambda _: True,
]


def search_spotify_tracks(sp_tracks, bridge_codes):
    for prio in SEARCH_PRIORITES:
        for sp_track in sp_tracks:
            if prio(sp_track) and (strip_str(sp_track['name'] + sp_track['artists'][0]['name'] + sp_track['album']['name']) in bridge_codes
                                   or not input(f'Is this ok? {sp_track['name']} by {sp_track['artists'][0]['name']} off of {sp_track['album']['name']}')):
                return sp_track
    return None


THUMBNAIL_SIZES = ['maxres', 'standard', 'high', 'medium', 'default']

# save album_urls for checking later
cursor.execute('SELECT id, source, uri FROM albums')
album_data = cursor.fetchall()
album_ids = [row[0] for row in album_data]
album_uri_matches = [row[1] + row[2] for row in album_data]

cursor.execute('select id, source, uri from artists where not uri is null')
artist_data = cursor.fetchall()
artist_ids = [row[0] for row in artist_data]
artist_uri_matches = [row[1] + row[2] for row in artist_data]

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
                    continue
                elif url[0:30] == 'https://open.spotify.com/track':
                    good_track = sp.track(url)
                elif url[0:32] == 'https://www.youtube.com/watch?v=' or url[0:17] == 'https://youtu.be/':
                    track_source = 'yt'
                    album_source = 'yt'
                    uri = url[(32 if url[8] == 'w' else 17):]
                    data = requests.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id='
                                        f'{uri[:uri.index('?')] if '?' in uri else uri}&key={YOUTUBE_API_KEY}').json()['items'][0]
                    runtime = iso_to_seconds(data['contentDetails']['duration'])

                    # siIvaGunner song
                    if data['snippet']['channelId'] == 'UC9ecwl3FTG66jIKA9JRDtmg':
                        dash_location = data['snippet']['title'].find('-')
                        title = data['snippet']['title'][:dash_location - 1]
                        album_title = data['snippet']['title'][dash_location + 2:]
                        album_type = 'album'
                        artists = [{'name': 'SiIvaGunner', 'uri': 'UC9ecwl3FTG66jIKA9JRDtmg', 'source': 'yt'}]
                        playlist_index = data['snippet']['description'].find('Playlist')
                        if playlist_index != -1:
                            album_url = data['snippet']['description'][playlist_index+10:data['snippet']['description'].find('\n', playlist_index+10)]
                        else:
                            album_url = input("Input playlist url: ")
                        album_uri = album_url[38:]
                        yt_api_type = 'playlists'
                    else:
                        corrected_title = input(f"If {lfm_title} is the wrong title, put it in correctly here: ")
                        title = corrected_title if corrected_title else lfm_title
                        album_type = input("Album type? ")
                        if album_type in ['single', 'video']:
                            album_title = title if album_type == 'single' else input("Album title? ")
                            album_uri = uri[:uri.index('?')] if '?' in uri else uri
                            yt_api_type = 'videos'
                        else:
                            album_url = input("Input playlist url: ")
                            if album_url[0:31] == 'https://open.spotify.com/album/':
                                sp_album = sp.album(album_url)
                                album_type = sp_album['album_type']
                                album_title = sp_album['name']
                                album_uri = sp_album['id']
                                album_source = 'sp'
                                image = sp_album['images'][0]['url'][24:]
                            else:
                                album_title = input("Album title? ")
                                album_uri = album_url[38:]
                                yt_api_type = 'playlists'
                        corrected_artist = input("If the primary artist's name is wrong, put it in correctly here: ")
                        artist_url = input("Channel ID or spotify URL of primary artist? ")
                        artists = [{'name': corrected_artist if corrected_artist else lfm_artist, 'uri': artist_url[0 if artist_url[0] == 'U' else 32:], 'source': 'sp' if artist_url[0] == 'U' else 'yt'}]
                        additional_artist_name = input("Other artists? Add name here: ")
                        while additional_artist_name:
                            artist_url = input("Channel ID or spotify URL of primary artist? ")  # @TODO: maybe convert this so it just takes the url and then converts the url just before adding it to the db
                            artists.append({'name': corrected_artist if corrected_artist else lfm_artist, 'uri': artist_url[0 if artist_url[0] == 'U' else 32:], 'source': 'sp' if artist_url[0] == 'U' else 'yt'})
                            additional_artist_name = input("Other artists? Add name here: ")

                    if album_source == 'yt':
                        thumbnails = requests.get(f'https://www.googleapis.com/youtube/v3/{yt_api_type}?part=snippet&id={album_uri}&key={YOUTUBE_API_KEY}').json()['items'][0]['snippet']['thumbnails']
                        for size in THUMBNAIL_SIZES:
                            if size in thumbnails:
                                image = thumbnails[size]['url'][23:-11]
                                break

                else:
                    raise Exception("Couldn't parse link, bruh, what'd you do???")

            if good_track:
                title = good_track['name']
                uri = good_track['id']
                track_source = 'sp'
                album_type = good_track['album']['album_type']
                album_title = good_track['album']['name']
                album_uri = good_track['album']['id']
                album_source = 'sp'
                image = good_track['album']['images'][0]['url'][24:]
                artists = [{'name': artist['name'], 'uri': artist['id'], 'source': 'sp'} for artist in good_track['artists']]
                runtime = int(good_track['duration_ms'] / 1000)

            cursor.execute('SELECT id FROM tracks WHERE uri = %s AND source = %s', [uri, track_source])
            results = cursor.fetchone()
            if results:
                track_id = results[0]
            else:
                input(f'Adding {title} by {artists[0]['name']} off {album_title}. Press Ctrl-C now if this is a mistake')
                album_uri_match = album_source + album_uri
                if album_uri_match in album_uri_matches:
                    album_id = album_ids[album_uri_matches.index(album_uri_match)]
                else:
                    cursor.execute('INSERT INTO albums (uri, name, type, source, image) VALUES (%s, %s, %s, %s, %s)', (album_uri, album_title, album_type, album_source, image))
                    album_id = cursor.lastrowid
                    album_uri_matches.append(album_uri_match)
                    album_ids.append(album_id)
                cursor.execute('INSERT INTO tracks (name, album_id, uri, runtime, source) VALUES (%s, %s, %s, %s, %s)', (title, album_id, uri, runtime, track_source))
                track_id = cursor.lastrowid

                primary = 1
                for artist in artists:
                    artist_uri = artist['uri']
                    artist_source = artist['source']
                    artist_uri_match = artist_source + artist_uri
                    if artist_uri_match in artist_uri_matches:
                        artist_id = artist_ids[artist_uri_matches.index(artist_uri_match)]
                    else:
                        cursor.execute('INSERT INTO artists (name, uri, source) VALUES (%s, %s, %s)', (artist['name'], artist_uri, artist_source))
                        artist_id = cursor.lastrowid
                        artist_uri_matches.append(artist_uri_match)
                        artist_ids.append(artist_id)
                    cursor.execute('INSERT INTO tracks_artists (track_id, artist_id, main) VALUES (%s, %s, %s)', (track_id, artist_id, primary))
                    primary = 0

            cursor.execute('INSERT INTO last_fm_str_tracks (last_fm_str, track_id) VALUES (%s, %s)', (bridge_codes[0], track_id))
            last_fm_str_dict[bridge_codes[0]] = track_id

        cursor.execute('INSERT INTO scrobbles (utc, track_id) VALUES (%s, %s)', (utc, track_id))
        last_added_utc = utc

        db.commit()
