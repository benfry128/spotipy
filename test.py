import utils
import db_one_time_scripts

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

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

# utils.compile_square_image(15, 80, urls)

# db_one_time_scripts.add_album_art(sp, db, cursor)

utils.compile_circle_image(1000, ['https://i.scdn.co/image/ab67616d0000b273f38c6b37a21334e22005b1f7',
                                  'https://i.scdn.co/image/ab67616d0000b2737d92a7b081f16384dfc13464',
                                  'https://i.scdn.co/image/ab67616d0000b2735b96a8c5d61be8878452f8f1',
                                  'https://i.scdn.co/image/ab67616d0000b2739a7c3dd5910b43e1f16c9ad1'
                                  ])

# @TODO: add function to get db records from a specific date period
# @TODO: update compile_circle_image to handle different size slices