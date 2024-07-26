import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

# cursor.execute('SELECT * from tracks where id < 2283 order by id ')

# tracks = cursor.fetchall()

# for t in tracks:
#     print(t[0])
#     track_url = t[4]
#     if track_url[8] == 'o':
#         track = sp.track(t[4])
#         album_type = track['album']['album_type']
#         url = track['album']['external_urls']['spotify']
#         name = track['album']['name']
#         runtime = int(track['duration_ms'] / 1000)
#     # else:
#         # album_type = input("Album type?")
#         # print(url)
#         # runtime = int(input("Duration? "))
#         print(album_type)
#         cursor.execute('UPDATE tracks SET album = %s where id = %s', (url, t[0]))

#         cursor.execute('SELECT * from albums where url = %s', [url])
#         if not cursor.fetchone():
#             cursor.execute('INSERT INTO albums (url, title, type) VALUES (%s, %s, %s)', (url, name, album_type))
#         db.commit()

# cursor.execute('SELECT * from albums where type = "single" order by url')

# albums = cursor.fetchall()

# for a in albums:
#     print("")
#     print(a[1])
#     cursor.execute('select * from tracks where album = %s', [a[0]])
#     tracks = cursor.fetchall()
#     for t in tracks:
#         print(t[1])
#         possible_tracks = sp.search(q=f'track:{t[1]} artist:{t[2]}', type='track', limit=10)['tracks']['items']
#         for track in possible_tracks:
#             if track['album']['album_type'] == 'album':
#                 print(f"{track['name']} by {track['artists'][0]['name']} off {track['album']['name']}. url is {track['external_urls']['spotify']}")

#         url = input('Which url? or enter an int')

#         if not url:
#             continue

#         good_track = sp.track(url)
#         input(good_track['album']['name'])
#         album_url = good_track['album']['external_urls']['spotify']

#         cursor.execute('select * from tracks where url = %s', [url])
#         old_record = cursor.fetchone()
#         if old_record:
#             utils.merge_tracks(old_record[0], t[0], db, cursor)
#             continue

#         cursor.execute('select * from albums where url = %s', [album_url])
#         old_album = cursor.fetchone()
#         if not old_album:
#             input(f"about to put in a new album: {good_track['album']['name']}, it's a {good_track['album']['album_type']}")
#             cursor.execute('INSERT INTO albums (url, title, type) VALUES (%s, %s, %s)', (album_url, good_track['album']['name'], good_track['album']['album_type']))

#         input(f"about to update this track's album ok? {url} {album_url}")
#         cursor.execute('update tracks set url = %s, album = %s where id = %s', (url, album_url, t[0]))
#         db.commit()

''''''

cursor.execute("select album from tracks where album not like '%spotify%' group by album;")

albums = cursor.fetchall()

for album in albums:
    print(album[0])
    

    # print(track[1])
    # print(track[0])
    # # print(track[3])
    # # title = track[3]
    # # print(track[4])
    # # url = input("URL? ")
    # # cursor.execute('INSERT INTO albums (url, title, type) VALUES (%s, %s, %s);', [url, title, 'single'])
    # cursor.execute('UPDATE tracks SET album = %s WHERE id = %s', [track[1], track[0]])
    # db.commit()