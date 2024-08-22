import utils

(db, cursor) = utils.db_setup()

print('checking for duplicates now')

dupe_checks = ['SELECT utc FROM '
               '(SELECT utc, track_id, '
               'LEAD(track_id, 1, 0) OVER (ORDER BY utc) AS idAfter, '
               'LAG(track_id, 1, 0) OVER (ORDER BY utc) AS idBefore, '
               '(LAG(utc, 1, 0) OVER (ORDER BY utc) - utc) * -1 AS timeBefore '
               'FROM scrobbles ORDER BY utc) t '
               'WHERE (idBefore = track_id OR idAfter = track_id) AND timeBefore < 60 AND timeBefore > 0;',
               'SELECT utc FROM '
               '(SELECT utc, track_id, '
               'LEAD(track_id, 1, 0) OVER (ORDER BY utc) AS idAfter, '
               'LAG(track_id, 1, 0) OVER (ORDER BY utc) AS idBefore, '
               'LEAD(utc, 1, 0) OVER (ORDER BY utc) - utc AS timeAfter '
               'FROM scrobbles ORDER BY utc) t '
               'WHERE (idBefore = track_id OR idAfter = track_id) AND timeAfter < 60 AND timeAfter > 0;'
               ]

for dupe_check in dupe_checks:
    cursor.execute(dupe_check)
    dupes = [record[0] for record in cursor.fetchall()]
    if dupes:
        print(dupes)
        if not input(f'About to delete {len(dupes)} records, you good with that?') == '':
            print("SKIPPED")
            continue
        cursor.execute(f'DELETE FROM scrobbles WHERE utc in ({str(dupes)[1:-1]})')
        db.commit()

# gotta check for dupes in tracks as well
cursor.execute('SELECT track, artist FROM track_album_main_artist GROUP BY track, artist HAVING COUNT(*) > 1;')
for (track, artist) in cursor.fetchall():
    print(f"Ok let's talk about {track} by {artist}")
    cursor.execute('SELECT track_id, album FROM track_album_main_artist WHERE track = %s AND artist = %s', (track, artist))
    dupe_records = cursor.fetchall()
    for (id, album) in dupe_records:
        print(f"This version is off the {album} album")

    keep_id = input("Which one would you like to keep? (0-indexed, press enter to change nothing")
    if keep_id:
        good_track = dupe_records[int(keep_id)][0]
        del dupe_records[int(keep_id)]
        for dupe_record in dupe_records:
            utils.merge_tracks(good_track, dupe_record[0], db, cursor)
