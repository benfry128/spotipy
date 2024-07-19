import utils
import os
import mysql.connector
import re

MY_USER_ID = os.getenv('ME_SPOTIFY_ID')
mysqlpwd = os.getenv('MYSQL_PWD')


sp = utils.spotipySetup()

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password=mysqlpwd,
    database='spotify_toolkit'
)

mycursor = mydb.cursor()

# sql = 'INSERT INTO scrobbles (time, image_url, artist, album, name) VALUES ("123", "abcd", "BEYONCE", "BEYONCE", "flawless")'

# mycursor.execute(sql)

# mydb.commit()

# print(mycursor.rowcount)

# utils.update_db(sp)


def only_an(str):
    return re.sub(r'\W+', '', str)


mycursor.execute('select name, artist from scrobbles group by name, artist')

results = mycursor.fetchall()

for result in results:
    goodName = only_an(result[0].lower())
    goodArtist = only_an(result[1].lower())
    

    possible_tracks = sp.search(q=f'track:{result[0].lower()} artist:{result[1].lower()}', type='track')['tracks']['items']
    if possible_tracks:
        tracks_to_check = 5 if len(possible_tracks) > 5 else len(possible_tracks)
        good = False
        for track in possible_tracks[0:tracks_to_check]:
            newName = only_an(track['name'].lower())
            newArtist = only_an(track['artists'][0]['name'].lower())
            if goodName == newName and goodArtist == newArtist:
                good = True
                print(f'FOUND IT {newName} by {newArtist}')
                utils.printDict(track)

                break
        if good:
            continue
    input(f'{goodName} by {goodArtist} is proving hard to find')
