import utils
from pprint import pprint


def merge_albums(urls, sp, db, cursor):
    # code to merge 2 albums

    titles = []
    album_dicts = []
    ids = []

    for url in urls:
        cursor.execute('SELECT id from albums where url = %s', [url])
        ids.append(cursor.fetchall()[0][0])

    input(ids)
    for url in urls:
        cursor.execute('SELECT * FROM tracks inner join albums on tracks.album_id = albums.id WHERE albums.url = %s', [url])
        titles.append([song[1] for song in cursor.fetchall()])
        tracks = sp.album_tracks(url)['items']
        track_titles = [track['name'] for track in tracks]
        track_urls = [track['external_urls']['spotify'] for track in tracks]
        album_dicts.append(dict(zip(track_titles, track_urls)))

    for t in titles:
        for ti in t:
            print(ti)
    input('Do you need to go and merge some tracks first????')

    for (url, album_dict, s) in zip(urls, album_dicts, titles):
        print(f"Let's see about this url: {url}")
        print(f'We have {len(s)} tracks in the db related to this url')
        good = True
        for title_set in titles:
            for title in title_set:
                if title not in album_dict:
                    print(f"couldn't find {title}")
                    good = False
                    break
            if not good:
                break
        if good:
            print("OK THAT'S GOOD!")
        else:
            print("NAH DON'T USE THIS ONE PROB")

    i = input("Ok you want to do it? Choose the index of the album you want to keep, or press enter to skip")
    if i:
        index = int(i)
        good_id = ids[index]
        album_dict = album_dicts[index]
        del ids[index]
        del titles[index]
        for (id, title_set) in zip(ids, titles):
            for title in title_set:
                print(f'{good_id}, {album_dict[title]}, {title}, {id}')
                cursor.execute('UPDATE tracks SET album_id = %s, url = %s where name = %s and album_id = %s', (good_id, album_dict[title], title, id))
                db.commit()


def add_albums_to_non_spotify_tracks(sp, db, cursor):
    cursor.execute("select album from tracks where album like '%spotify%' group by album;")

    albums = cursor.fetchall()

    for album in albums:
        print(album[0])

        sp_album = sp.album(album[0])
        pprint(sp_album)
        input("HI")
        url = input("URL? ")
        a_type = input("type? ")
        cursor.execute('INSERT INTO albums (url, title, type) VALUES (%s, %s, %s);', [url, album[0], a_type])
        cursor.execute('UPDATE tracks SET album = %s WHERE album = %s', [url, album[0]])
        db.commit()


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


def add_runtime_and_spotify_track_to_tracks_but_also_I_changed_it_so_it_adds_albums_back(sp, db, cursor):
    cursor.execute('SELECT * from tracks order by id ')

    tracks = cursor.fetchall()

    for t in tracks:
        print(t[0])
        track_url = t[4]
        if track_url[8] == 'o':
            track = sp.track(t[4])
            album_type = track['album']['album_type']
            url = track['album']['external_urls']['spotify']
            name = track['album']['name']
            # runtime = int(track['duration_ms'] / 1000)
        # else:
            # album_type = input("Album type?")
            # print(url)
            # runtime = int(input("Duration? "))
            print(album_type)
            cursor.execute('UPDATE tracks SET album = %s where id = %s', (url, t[0]))

            cursor.execute('SELECT * from albums where url = %s', [url])
            if not cursor.fetchone():
                cursor.execute('INSERT INTO albums (url, title, type) VALUES (%s, %s, %s)', (url, name, album_type))
            db.commit()


def swap_out_clean_versions_of_albums(sp, db, cursor):
    sp_albums = utils.sp_albums(sp, cursor)

    for sp_album in sp_albums:
        if not utils.album_explicit(sp_album):
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
        cursor.execute('update albums set image = %s where url = %s', [album['images'][0]['url'], album['external_urls']['spotify']])

    db.commit()