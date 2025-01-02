import utils
from datetime import datetime
from pprint import pprint

sp = utils.spotipy_setup()

(db, cursor) = utils.db_setup()

cursor.execute('select utc, album from scrobbles join all_urls on scrobbles.track_id = all_urls.track_id where utc < 1735711200;')

d = []
totals = []
for hour in range(7):
    d.append({})
    totals.append(0)

for (utc, name) in cursor.fetchall():
    if 1710057600 < utc < 1730620800:
        offset = 14400
    else:
        offset = 18000

    t = datetime.fromtimestamp(utc - offset)

    hour = t.weekday()

    if name not in d[hour]:
        d[hour][name] = 1
    else:
        d[hour][name] += 1

    totals[hour] += 1

for hour in range(7):

    sorted_items = sorted(d[hour].items(), key=lambda kv: (kv[1], kv[0]))

    pprint(sorted_items[-10:])
    print(hour)
