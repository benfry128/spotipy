import utils

sp = utils.spotipySetup()

(db, cursor) = utils.db_setup()

# code to merge 2 albums

urls = ['https://open.spotify.com/album/5MqyhhHbT13zsloD3uHhlQ', 'https://open.spotify.com/album/53PBYiedQrASAs5sy63JqT']

titles = []
album_dicts = []
total_tracks = []

for url in urls:
    cursor.execute('SELECT * FROM tracks WHERE album = %s', [url])
    titles.append([song[1] for song in cursor.fetchall()])
    tracks = sp.album_tracks(url)['items']
    track_titles = [track['name'] for track in tracks]
    track_urls = [track['external_urls']['spotify'] for track in tracks]
    album_dicts.append(dict(zip(track_titles, track_urls)))


for t in titles:
    for ti in t:
        print(ti)
input('Do you need to go and merge some tracks first????')


for (url, album_dict, s) in zip(urls, album_dicts, titles):
    print(f"Let's see about this url: {url}")
    print(f'We have {len(s)} tracks in the db related to this url')
    good = True
    for title_set in titles:
        for title in title_set:
            if title not in album_dict:
                print(f"couldn't find {title}")
                good = False
                break
        if not good:
            break
    if good:
        print("OK THAT'S GOOD!")
    else:
        print("NAH DON'T USE THIS ONE PROB")


i = input("Ok you want to do it? Choose the index of the album you want to keep, or press enter to skip")
if i:
    index = int(i)
    good_url = urls[index]
    album_dict = album_dicts[index]
    del urls[index]
    del titles[index]
    for (url, title_set) in zip(urls, titles):
        for title in title_set:
            cursor.execute('UPDATE tracks SET album = %s, url = %s where name = %s and album = %s', (good_url, album_dict[title], title, url))
            db.commit()

    # do the merging here
