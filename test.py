import utils
from pprint import pprint

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

tracks = sp.search(q=f'track:I Write Sins Not Tragedies artist:Panic! at the Disco', type='track', limit=10)['tracks']['items']

pprint(tracks[0:3])