import utils
import os
import mysql.connector

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

mycursor.execute('select * from tracks where id > 2660 order by id')

for track in mycursor.fetchall():
    uri = track[4]
    print(uri)
    if uri[8] == 'o':
        sp_track = sp.track(uri)
        name = sp_track['name']
        artist = sp_track['artists'][0]['name']
        album = track[3]
    else:
        name = input("Name\n")
        artist = input("Artist\n")
    print("getting ready")
    mycursor.execute('update tracks set name = %s, artist = %s where id = %s', 
                     (name, artist, track[0]))
    mydb.commit()

# utils.sanitize_db()