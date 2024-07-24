import utils
import os

MY_USER_ID = os.getenv('ME_SPOTIFY_ID')
mysqlpwd = os.getenv('MYSQL_PWD')


sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

utils.update_db(sp, db, cursor)
