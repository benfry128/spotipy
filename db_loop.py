import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

cursor.execute('SELECT * from tracks where id > 2282 order by id ')

tracks = cursor.fetchall()

for t in tracks:
    print(t[0])
    track_url = t[4]
    if track_url[8] == 'o':
        track = sp.track(t[4])
        album_type = track['album']['album_type']
        url = track['album']['external_urls']['spotify']
        name = track['album']['name']
        runtime = int(track['duration_ms'] / 1000)
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
