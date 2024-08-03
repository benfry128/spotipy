import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

x = 'Tyler, The Creator'
y = 'Dreamville, JID, EARTHGANG'

bridge_codes = [y]
remove_comma_from_artist = y
while ', ' in remove_comma_from_artist:
    remove_comma_from_artist = remove_comma_from_artist[0:remove_comma_from_artist.rindex(', ')]
    bridge_codes.append(remove_comma_from_artist)

print(bridge_codes)