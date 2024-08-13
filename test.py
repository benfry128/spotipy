import utils
import random

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

cursor.execute('''select count(utc), image from
scrobbles join track_album_main_artist on scrobbles.track_id = track_album_main_artist.track_id
join albums on track_album_main_artist.album_id = albums.id
where not image = ''
group by artist, album, image order by count(utc) desc limit 225;
''')
results = [{'count': row[0], 'url': row[1]} for row in cursor.fetchall()]

urls = []
for result in results:
    urls.extend([result['url']] * int(result['count'] / 25))
urls = urls[0:225]
random.shuffle(urls)

utils.compile_image(15, 80, urls)
