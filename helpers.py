import spotipy
import re
import requests

from cs50 import SQL
from spotipy import util
from spotipy.oauth2 import SpotifyOAuth
from bs4 import BeautifulSoup

db = SQL("sqlite:///tracklist.db")
database = db.execute('SELECT * FROM tracklist')

def searching_tracks():
    """Searching tracks in spotify and return tracks id."""

    scope = "user-library-read, playlist-modify-public, playlist-modify-private"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    str = 0
    not_found = 0

    for group in (database[pos:pos + 100] for pos in range(0, len(database), 100)):
        for i in range(len(group)):
            q = group[i]["artist"] + " " + group[i]["track"].replace("\"", "")
            q = re.sub("[\(\[].*?[\)\]]", "", q)
            str += 1

            result = sp.search(q, limit=1, type='track')
            if result["tracks"]["total"] == 0:
                not_found = + 1
                continue

            db.execute("UPDATE tracklist SET uri = ? WHERE id = ?", result['tracks']['items'][0]['id'], group[i]['id'])
        

    print(f"{str - not_found} tracks added")
    print(f"{not_found} items were not found")


def scrape():
    """Scraping website"""
    db = SQL("sqlite:///tracklist.db")
    url = 'https://pitchfork.com/reviews/best/tracks/?page='
    new_tracklist = []
    new_track = {}
    page = 1
    ctr = 0
    no_more_new_tracks = 0

    # loop to iterate pages until status not 200 or old tracks are exist
    while True:
        # check if there are already old tracks in the page
        response = requests.get(url + str(page))
        if response.status_code not in range(200, 299):
            raise Exception("Could not access website.")
        else:
            soup = BeautifulSoup(response.content, 'html.parser')

            # scraping website for tracks info
            artists = soup.find_all('ul', {'class': 'artist-list'})
            tracks = (soup.find_all('h2', {'class': 'title'})) + (
                soup.find_all('h2', {'class': 'track-collection-item__title'}))
            dates = soup.find_all('time', {'class': 'pub-date'})

            # search if db already has tracks from page
            database = db.execute('SELECT * FROM tracklist')

            for i in range(len(tracks)):
                # adding new tracks to list of dictionaries
                if not next((item for item in reversed(database) if item["artist"] == str(artists[i].li.string) and item["track"].strip('“”') == str(tracks[i].string).strip('“”')), False):
                    new_track["artist"] = str(artists[i].li.string)
                    new_track["track"] = str(tracks[i].string)
                    new_track["year"] = int(str(dates[i]['datetime'])[:4])
                    new_tracklist.append(new_track.copy())
                    ctr += 1

                # if there are old tracks in the page break the loop
                else:
                    print(f"There are {ctr} new tracks")
                    no_more_new_tracks = 1
                    break
            page += 1
        if no_more_new_tracks == 1:
            # if page not exist or there are old tracks in the page add new tracks to db
            for i in reversed(range(len(new_tracklist))):
                db.execute("INSERT INTO tracklist (artist, track, year) VALUES (?, ?, ?)",
                           new_tracklist[i]['artist'], new_tracklist[i]['track'], new_tracklist[i]['year'])
            print("Adding new tracks succesful")
            database += reversed(new_tracklist)
            return reversed(database)


def get_tracklist_year(year):
    db = SQL("sqlite:///tracklist.db")
    tracklist_year = db.execute(
        f"SELECT * FROM tracklist WHERE year='{year}' ORDER BY id DESC")
    return tracklist_year


def get_number_of_years():
    db = SQL("sqlite:///tracklist.db")
    list_of_years = db.execute("SELECT DISTINCT year FROM tracklist ORDER BY year DESC")
    return [d['year'] for d in list_of_years]
