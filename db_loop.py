import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

cursor.execute('SELECT * from tracks order by id')

tracks = cursor.fetchall()

for t in tracks:
    url = t[4]
    if url[8] == 'o':
        spotify_track = 1
        track = sp.track(t[4])
        runtime = int(track['duration_ms'] / 1000)
    else:
        spotify_track = 0
        print(url)
        runtime = int(input("Duration? "))

    cursor.execute('UPDATE tracks SET runtime = %s, spotify_track = %s where id = %s', (runtime, spotify_track, t[0]))
    db.commit()
