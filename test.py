import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

utils.update_db(sp, db, cursor)