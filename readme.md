# Music Toolkit

Music Toolkit is a project I built to explore, quantify, and analyze my listening habits. 
It interfaces with the Spotify, Lastfm, and Youtube APIs. 
Some of the scripts in this project may be of interest to others, but a decent amount if it is only relevant to my own personal music software usage.
In particular, the scripts labeled `db` are for use with a personal MySQL database I built to log my listening history.
Improper usage of some scripts (like shuffle.py) might mess up your own playlists. You have been warned.

## Installation and Usage

- Clone the repo to your local machine.
- Use a virtual environment to install the necessary packages. 
- Create a Project on the Spotify Developer Dashboard (follow the instructions [here](https://spotipy.readthedocs.io/en/2.24.0/#authorization-code-flow)), then grab the client id and client secret and put them in a .env file as `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.
- To use Youtube API- and Lastfm API-related features (mostly in the db scripts), you'll need to add a `LAST_FM_API_KEY` and a `YOUTUBE_API_KEY` to the .env file as well. You'll need to generate these on their respective websites.  

## License

[MIT](https://choosealicense.com/licenses/mit/)
