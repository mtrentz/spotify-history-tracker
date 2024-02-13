# Import spotipy library
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import json

load_dotenv()

# album_id = "4JuWR37EaMsPMzbUX7RAzq"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-library-read"))

# album = sp.album(album_id)

# # Save to file
# with open("album.json", "w") as file:
#     json.dump(album, file, indent=2)


# track_id = "4LKhv5yZGyJkrGnNh9migl"

# track = sp.track(track_id)

# # Save to file
# with open("track.json", "w") as file:
#     json.dump(track, file, indent=2)


# # Get all genre seeds and save to file
# genres = sp.recommendation_genre_seeds()
# with open("genres.json", "w") as file:
#     json.dump(genres, file, indent=2)


# Get Recently Played
recently_played = sp.current_user_recently_played()

with open("recently_played.json", "w") as file:
    json.dump(recently_played, file, indent=2)

# # Go over all albums and save its id
# album_ids = []

# for item in recently_played["items"]:
#     album = item["track"]["album"]
#     album_ids.append(album["id"])

# # Request batch of albums
# albums = sp.albums(album_ids[:20])

# # Save to file
# with open("recently_played_albums.json", "w") as file:
#     json.dump(albums, file, indent=2)
