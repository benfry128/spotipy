import utils
import random
import db_one_time_scripts
import requests
from pprint import pprint

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

# cursor.execute('SELECT id, url FROM albums WHERE url like "%youtu.be%"')
# rows = cursor.fetchall()

# THUMBNAIL_SIZES = ['maxres', 'standard', 'high', 'medium', 'default']

# for row in rows:
#     db_id = row[0]
#     yt_id = row[1][17:]
#     r = requests.get(f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={yt_id}&key={utils.YOUTUBE_API_KEY}')
#     pprint(r.json())
#     thumbnails = r.json()['items'][0]['snippet']['thumbnails']
#     for size in THUMBNAIL_SIZES:
#         if size in thumbnails:
#             cursor.execute('UPDATE albums SET image = %s where id = %s', [thumbnails[size]['url'], db_id])
#             db.commit()
#             break

# cursor.execute('SELECT id, url FROM albums WHERE url like "%youtube.com/playlist%"')
# rows = cursor.fetchall()

# THUMBNAIL_SIZES = ['maxres', 'standard', 'high', 'medium', 'default']

# for row in rows:
#     db_id = row[0]
#     yt_id = row[1][38:]
#     r = requests.get(f'https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={yt_id}&key={utils.YOUTUBE_API_KEY}')
#     thumbnails = r.json()['items'][0]['snippet']['thumbnails']
#     for size in THUMBNAIL_SIZES:
#         if size in thumbnails:
#             cursor.execute('UPDATE albums SET image = %s where id = %s', [thumbnails[size]['url'], db_id])
#             db.commit()
#             break

# r = requests.get(f'https://www.googleapis.com/youtube/v3/playlists?part=snippet&id=PL3q9ip9kYA-CMviRiuVmCrpermQVxPgkj&key={utils.YOUTUBE_API_KEY}')

# pprint(r.json())

# cursor.execute('''select count(utc), image from
# scrobbles join track_album_main_artist on scrobbles.track_id = track_album_main_artist.track_id
# join albums on track_album_main_artist.album_id = albums.id
# where not image = '' and artist not in ('Mikel', 'Helynt', 'Besso0', 'Amos Roddy',
# 'Joris de Man', 'Lena Raine', 'Andrew Prahlow', 'GENTLE LOVE',
# 'Slofi', 'ImRuscelOfficial', 'The Flight')
# group by artist, album, image order by count(utc) desc limit 250;
# ''')
# results = [{'count': row[0], 'url': row[1]} for row in cursor.fetchall()]

# urls = []
# for result in results:
#     urls.extend([result['url']] * int(result['count'] / 20))
# urls = urls[0:225]
# random.shuffle(urls)

# utils.compile_image(15, 80, urls)

# db_one_time_scripts.add_album_art(sp, db, cursor)
