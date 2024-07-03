import utils
import random
import os
from datetime import datetime, timezone

sp = utils.spotipySetup('playlist-read-private playlist-read-collaborative user-read-playback-state playlist-modify-public')

# SETTINGS
EXCLUDE_COLLAB_PLAYLISTS = True
EXCLUDE_OTHERS_PLAYLISTS = True
EXPLICIT_ALLOWED = False
MY_USER_ID = os.getenv('ME_SPOTIFY_ID')
USER_ID_INPUT = input('User id? ')
USER_ID = MY_USER_ID if USER_ID_INPUT == 'mine' else USER_ID_INPUT

user = sp.user(USER_ID)

result = sp.user_playlists(USER_ID)

playlists = utils.getAllPlaylists(USER_ID, sp)

letters = 'abcdefghijklmnopqrstuvwxyz'
letter_list = list(letters)
letterDict = {}

for letter in letters:
    letterDict[letter] = {}

for playlist in playlists:
    if (EXCLUDE_COLLAB_PLAYLISTS and playlist['collaborative']) or (EXCLUDE_OTHERS_PLAYLISTS and not playlist['owner']['id'] == USER_ID):
        print(f"{playlist['name']} EXCLUDED")
        continue
    readPlaylist = input(f"Include playlist {playlist['name']}? (y/n/s to skip the rest) ")
    if readPlaylist == 's':
        break
    elif readPlaylist != 'y':
        continue
    print(playlist['name'])
    tracks = utils.getAllTracks(playlist['uri'], sp)

    for track in tracks:
        if not track['track'] or (track['track']['explicit'] and not EXPLICIT_ALLOWED):
            continue
        track_name = track['track']['name']
        track_id = track['track']['uri']
        first_letter = 0
        for letter in track_name:
            if letter.lower() in letter_list:
                first_letter = letter.lower()
                break
        if not first_letter:
            continue
        # track_artist = track['track']['artists'][0]['name']

        if track_id in letterDict[first_letter]:
            letterDict[first_letter][track_id] += 1
        else:
            letterDict[first_letter][track_id] = 1

# loop through letter dict to choose a song from

allLetters = True
for letter in letterDict:
    if not letterDict[letter].keys():
        allLetters = False
        break

final_uris = []

if allLetters or input("Playlist will not be complete, continue? (y/n) ") == 'y':
    for letter in letterDict:
        maxFreq = 0
        uris = []

        for uri in letterDict[letter]:
            uris.append(uri)
        if uris:
            final_uris.append(uris[random.randint(0, len(uris) - 1)])

    a_to_z_playlist = sp.user_playlist_create(MY_USER_ID, f'A to Z - {user['display_name']} - {datetime.now(tz=timezone.utc).strftime('%d/%m/%Y')}')

    result = sp.user_playlist_add_tracks(MY_USER_ID, a_to_z_playlist['uri'], final_uris)
