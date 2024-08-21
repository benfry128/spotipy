import utils
from pprint import pprint
import requests


def change_singles_to_albums(sp, db, cursor):
    cursor.execute('SELECT * from albums where type = "single" order by url')

    albums = cursor.fetchall()

    for a in albums:
        print("")
        print(a[1])
        cursor.execute('select * from tracks where album = %s', [a[0]])
        tracks = cursor.fetchall()
        for t in tracks:
            print(t[1])
            possible_tracks = sp.search(q=f'track:{t[1]} artist:{t[2]}', type='track', limit=10)['tracks']['items']
            for track in possible_tracks:
                if track['album']['album_type'] == 'album':
                    print(f"{track['name']} by {track['artists'][0]['name']} off {track['album']['name']}. url is {track['external_urls']['spotify']}")

            url = input('Which url? or enter an int')

            if not url:
                continue

            good_track = sp.track(url)
            input(good_track['album']['name'])
            album_url = good_track['album']['external_urls']['spotify']

            cursor.execute('select * from tracks where url = %s', [url])
            old_record = cursor.fetchone()
            if old_record:
                utils.merge_tracks(old_record[0], t[0], db, cursor)
                continue

            cursor.execute('select * from albums where url = %s', [album_url])
            old_album = cursor.fetchone()
            if not old_album:
                input(f"about to put in a new album: {good_track['album']['name']}, it's a {good_track['album']['album_type']}")
                cursor.execute('INSERT INTO albums (url, title, type) VALUES (%s, %s, %s)', (album_url, good_track['album']['name'], good_track['album']['album_type']))

            input(f"about to update this track's album ok? {url} {album_url}")
            cursor.execute('update tracks set url = %s, album = %s where id = %s', (url, album_url, t[0]))
            db.commit()


def swap_out_clean_versions_of_albums(sp, db, cursor):
    sp_albums = utils.sp_albums(sp, cursor)

    for sp_album in sp_albums:
        if not utils.album_explicit_and_few_artists(sp_album):
            print(f'Album {sp_album['name']} is clean')
            title = sp_album['name']
            artist = sp_album['artists'][0]['name']
            other_versions = sp.search(f'album:{title} artist:{artist}', limit=5, type='album')['albums']['items']
            if type(other_versions) is list:
                for album in other_versions:
                    if not album['external_urls']['spotify'] == sp_album['external_urls']['spotify'] and album['name'] == sp_album['name']:
                        print(album['external_urls']['spotify'])
                        if not input('Maybe this one would be better?'):
                            cursor.execute('insert into albums (url, title, type) values (%s, %s, %s)', [album['external_urls']['spotify'], album['name'], album['album_type']])
                            cursor.execute('update tracks set album = %s where album = %s', [album['external_urls']['spotify'], sp_album['external_urls']['spotify']])
                            db.commit()


def add_popularity_scores(sp, db, cursor):
    sp_tracks = utils.sp_tracks(sp, cursor)

    for track in sp_tracks:
        print(f'{track['name']}\n{track['popularity']}')
        cursor.execute('update tracks set popularity = %s where url = %s', [track['popularity'], track['external_urls']['spotify']])

    db.commit()


def add_album_art(sp, db, cursor):
    albums = utils.sp_albums(sp, cursor)

    for album in albums:
        cursor.execute('update albums set image = %s where uri = %s', [album['images'][0]['url'], album['id']])

    db.commit()

    cursor.execute('SELECT id, url FROM albums WHERE url like "%youtu.be%"')
    rows = cursor.fetchall()

    THUMBNAIL_SIZES = ['maxres', 'standard', 'high', 'medium', 'default']

    for row in rows:
        db_id = row[0]
        yt_id = row[1][17:]
        r = requests.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={yt_id}&key={utils.YOUTUBE_API_KEY}')
        pprint(r.json())
        thumbnails = r.json()['items'][0]['snippet']['thumbnails']
        for size in THUMBNAIL_SIZES:
            if size in thumbnails:
                cursor.execute('UPDATE albums SET image = %s where id = %s', [thumbnails[size]['url'], db_id])
                db.commit()
                break

    cursor.execute('SELECT id, url FROM albums WHERE url like "%youtube.com/playlist%"')
    rows = cursor.fetchall()

    THUMBNAIL_SIZES = ['maxres', 'standard', 'high', 'medium', 'default']

    for row in rows:
        db_id = row[0]
        yt_id = row[1][38:]
        r = requests.get(f'https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={yt_id}&key={utils.YOUTUBE_API_KEY}')
        thumbnails = r.json()['items'][0]['snippet']['thumbnails']
        for size in THUMBNAIL_SIZES:
            if size in thumbnails:
                cursor.execute('UPDATE albums SET image = %s where id = %s', [thumbnails[size]['url'], db_id])
                db.commit()
                break
