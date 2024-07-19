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

# sql = 'INSERT INTO scrobbles (time, image_url, artist, album, name) VALUES ("123", "abcd", "BEYONCE", "BEYONCE", "flawless")'

# mycursor.execute(sql)

# mydb.commit()

# print(mycursor.rowcount)

# utils.update_db(sp)

# mycursor.execute('select distinct artist from scrobbles')

# artists = [artist[0] for artist in mycursor.fetchall()]

# print(artists)

# for artist in artists:

print(utils.getRecentTracks(1, 1, sp))