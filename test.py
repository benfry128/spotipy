import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()


results = sp.current_user_recently_played(limit=50, before=1722285562608)
print(results['next'])

for item in results['items']:
    print(item['track']['name'])