import utils
import os

sp = utils.spotipy_setup()

db, cursor = utils.db_setup()

days = int(input("How many days back would you like to go? "))

MY_USER_ID = os.getenv('ME_SPOTIFY_ID')

recents = utils.get_recent_tracks(days, 0, cursor)

recent_dict = {}
for recent in recents:
    name_and_artist = f'{recent['track']} by {recent['artist']}'.lower()
    if name_and_artist in recent_dict:
        recent_dict[name_and_artist] += 1
    else:
        recent_dict[name_and_artist] = 1

playlists = utils.getAllPlaylists(MY_USER_ID, sp)

for playlist in playlists:
    print("~" * 200)
    print("~" * 200)
    name = playlist['name']
    uri = playlist['uri']

    analyze = input(f'Analyze playlist "{name}"? (y/n/s to skip all) ')
    while analyze != 'y' and analyze != 'n' and analyze != 's':
        analyze = input(f'You idiot.\nAnalyze playlist "{name}"? (y/n/s to skip all) ')

    if analyze == 's':
        break
    elif analyze == 'n':
        continue

    tracks = utils.getAllTracks(uri, sp)

    print(f"Analyzing {len(tracks)} tracks from playlist{name}")

    least_plays = 1000000
    most_plays = 0
    least_list = []
    most_list = []

    for track in tracks:
        name_and_artist = f'{track['name']} by {track['artists'][0]['name']}'.lower()
        uri = track['uri']
        if name_and_artist in recent_dict:
            frequency = recent_dict[name_and_artist]
            if frequency > most_plays:
                most_plays = frequency
                most_list = [name_and_artist]
            elif frequency == most_plays:
                most_list.append(name_and_artist)
            if frequency < least_plays:
                least_plays = frequency
                least_list = [name_and_artist]
            elif frequency == least_plays:
                least_list.append(name_and_artist)
        else:
            if least_plays > 0:
                least_list = [name_and_artist]
            else:
                least_list.append(name_and_artist)
            least_plays = 0
    print(f'\nThe most times any song was played was {most_plays}\nThose were: ')
    for track in most_list:
        print(track)
    print(f'\nThe least times any song was played was {least_plays}\nThose were: ')
    for track in least_list:
        print(track)
