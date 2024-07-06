import utils
import os

sp = utils.spotipySetup()

MY_USER_ID = os.getenv('ME_SPOTIFY_ID')
USER_ID_INPUT = input('User id? ')
USER_ID = MY_USER_ID if USER_ID_INPUT == 'mine' else USER_ID_INPUT

playlists = utils.getAllPlaylists(USER_ID, sp)

skip_playlists = ['BangerS', 'VibeS', 'ThonkerS', 'Classics - Hi', 'Classics - Lo', 'To Listen', ]

artists = {}

for playlist in playlists:
    if playlist['collaborative'] or not playlist['owner']['id'] == USER_ID or playlist['name'] in skip_playlists:
        print(f"{playlist['name']} EXCLUDED")
        continue

    print(playlist['name'])
    tracks = utils.getAllTracks(playlist['uri'], sp)
    for track in tracks:
        for artist in track['artists']:
            artist_uri = artist['uri']
            if artist_uri in artists:
                artists[artist_uri] += 1
            else:
                artists[artist_uri] = 1
    utils.printDict(artists)
