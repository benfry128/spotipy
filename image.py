# from PIL import Image
import requests
import shutil

url = 'https://lastfm.freetls.fastly.net/i/u/300x300/d13647f58c66d516599fba9ac7c7c3ac.jpg'
response = requests.get(url, stream=True)
with open('img.png', 'wb') as out_file:
    shutil.copyfileobj(response.raw, out_file)
del response
