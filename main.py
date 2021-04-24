from bs4 import BeautifulSoup
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# Acquire a date from the user
date = input("Which year do you want to travel to? Type the date in this format YYYY-MM-DD: ")

# Place the user date in billboard url
billboard = f'https://www.billboard.com/charts/hot-100/{date}'

# Get the html data from billboard
response = requests.get(billboard)
site = response.text

soup = BeautifulSoup(site, 'html.parser')

# Get the span data and get the string value in the spans (artists and track titles)
# And clean the returned lists of artists (some contain multiple artists but in order for spotify to
# recognize the artist we just want to find the first artist in a duet
spans_artists = soup.find_all('span', class_='chart-element__information__artist')
artists = [artist.getText() for artist in spans_artists]

spans_titles = soup.find_all('span', class_='chart-element__information__song')
titles = [title.getText() for title in spans_titles]

artists = [artists[i].split('Featuring')[0].strip() for i in range(len(artists))]
artists = [artists[i].split('&')[0].strip() for i in range(len(artists))]
artists = [artists[i].split('With')[0].strip() for i in range(len(artists))]

# Place the number of artists and titles into a dictionary with artists as keys and songs as values
# if the artist is already in the dictionary (when the artist has multiple top 100 songs on a given date)
# we add it to the value list
query = {}
for i in range(len(artists)):
    query.setdefault(artists[i], [])
    query[artists[i]].append(titles[i])

# spotify requires a scope if which the program will be modifying a user profile
scope = 'playlist-modify-public'

# stored spotify credentials
client_id = os.environ['SPOTIPY_CLIENT_ID']
client_secret = os.environ['SPOTIPY_CLIENT_SECRET']
redirect_uri = os.environ['SPOTIPY_REDIRECT_URI']

# Establish a connection to spotify api
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        scope=scope
    )
)

# acquire a uri based on each artist and track in the in dictionary
uri = ''
# a uri is stored in a list of uris which will be passed through a sp method
uris = []
for artist, track in query.items():
    for i in range(len(track)):
        try:
            uri = sp.search(q=f"track:{track[i]} artist:{artist}", type='track')['tracks']['items'][0]['uri']
        except IndexError:
            # If the given song from billboard doesn't exist on spotify
            pass
        finally:
            uris.append(uri)

# get the current user's id (this will allow us to connect to their account to create a playlist with the uris)
user_id = sp.current_user()['id']

# create a new playlist
playlist_id = sp.user_playlist_create(user_id, f"{date} Billboard 100", description=f'Top 100 Songs from {date}')['id']

# add items to the new playlist
sp.playlist_add_items(playlist_id, uris, 0)
