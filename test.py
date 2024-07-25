import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

utils.merge_tracks(2437, 256, db, cursor)