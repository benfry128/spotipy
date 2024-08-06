import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

# sp_tracks = utils.sp_tracks(sp, cursor)

# print(sp_tracks[0])

cursor.execute('select url from artists order by id')
artist_urls = [row[0] for row in cursor.fetchall()]

cursor.execute('select * from tracks where tracks.name like "%feat.%" and url not like "%spotify%";')
result = cursor.fetchall()

for row in result:
    print(row[1])
    url = input("url? ")
    while url:
        if url in artist_urls:
            artist_id = artist_urls.index(url) + 1
        else:
            cursor.execute('INSERT INTO artists (name, url) VALUES (%s, %s)', (input(f"WHO's this artist? {url}"), url))
            artist_urls.append(url)
            artist_id = len(artist_urls)
        cursor.execute('INSERT INTO tracks_artists (track_id, artist_id, pri) VALUES (%s, %s, %s)', (row[0], artist_id, 0))
        db.commit()
        url = input("url? ")

    # url = row[2]


#     artist = row[0]
#     print(artist)
#     artist_url = input("url? ")
#     cursor.execute('UPDATE tracks SET artist = %s where artist = %s', (artist_url, artist))
#     db.commit()


# for sp_track in sp_tracks:
#     primary = 1
#     for artist in sp_track['artists']:
#         url = artist['external_urls']['spotify']
#         if url in artist_urls:
#             artist_id = artist_urls.index(url) + 1
#         else:
#             cursor.execute('INSERT INTO artists (name, url) VALUES (%s, %s)', (artist['name'], url))
#             artist_urls.append(url)
#             artist_id = len(artist_urls)
#         cursor.execute('INSERT INTO tracks_artists (track_id, artist_id, pri) VALUES (%s, %s, %s)', (track_id_dict[sp_track['external_urls']['spotify']], artist_id, primary))
#         primary = 0
#     db.commit()