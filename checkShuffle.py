import utils

sp = utils.spotipySetup()

days = int(input("How many days back would you like to go? "))

my_id = '31tnaej2hznzuj25tx2p2lf7p4xy'

recents = utils.getRecentTracks(days, 0, sp)

recentDict = {}
for recent in recents:
    nameAndArtist = f'{recent['name']} {recent['artist']['#text']}'.lower()
    if nameAndArtist in recentDict:
        recentDict[nameAndArtist] += 1
    else:
        recentDict[nameAndArtist] = 1

playlists = utils.getAllPlaylists(my_id, sp)

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

    leastPlays = 1000000
    mostPlays = 0
    leastList = []
    mostList = []

    for track in tracks:
        trackName = track['name']
        trackArtist = track['artists'][0]['name']
        trackId = track['uri']
        code = f'{trackName} {trackArtist}'.lower()
        if code in recentDict:
            frequency = recentDict[code]
            if frequency > mostPlays:
                mostPlays = frequency
                mostList = [f'{trackName} by {trackArtist}']
            elif frequency == mostPlays:
                mostList.append(f'{trackName} by {trackArtist}')
            if frequency < leastPlays:
                leastPlays = frequency
                leastList = [f'{trackName} by {trackArtist}']
            elif frequency == leastPlays:
                leastList.append(f'{trackName} by {trackArtist}')
        else:
            if leastPlays > 0:
                leastList = [f'{trackName} by {trackArtist}']
            else:
                leastList.append(f'{trackName} by {trackArtist}')
            leastPlays = 0
    print(f'The most times any song was played was {mostPlays}\nThose were: ')
    for track in mostList:
        print(track)
    print(f'The least times any song was played was {leastPlays}\nThose were: ')
    for track in leastList:
        print(track)
