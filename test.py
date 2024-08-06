import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

cursor.execute('SELECT id, url FROM albums')
album_urls = [(row[0], row[1]) for row in cursor.fetchall()]

print(album_urls[0:10])

for (id, url) in album_urls:
    cursor.execute('update tracks set album = %s where album = %s', (id, url))
    db.commit()
