import utils
from datetime import datetime
from pprint import pprint
import matplotlib.pyplot as plt

sp = utils.spotipy_setup()

(db, cursor) = utils.db_setup()

cursor.execute('select count(*), popularity from scrobbles join tracks on track_id = id where utc < 1735711200 and popularity is not null group by track_id order by count(*) desc;')

xs_and_ys = cursor.fetchall()

plays = [x_and_y[0] for x_and_y in xs_and_ys]
popularity = [x_and_y[1] for x_and_y in xs_and_ys]

fig, ax = plt.subplots()

ax.scatter(popularity, plays)

ax.set_xlabel('Popularity')
ax.set_ylabel('Play Count')

plt.show()
