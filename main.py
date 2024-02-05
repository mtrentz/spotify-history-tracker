import os
import json
import spotipy
import argparse
from spotipy.oauth2 import SpotifyOAuth
from db import close_connection
from logger import logger
from models import (
    insert_artist,
    insert_album,
    insert_track,
    insert_album_artist,
    insert_track_artist,
    insert_genre,
    insert_album_genre,
    insert_artist_genre,
    insert_streaming_history,
    get_object_by_id,
    get_genre_id,
    is_streaming_history_added,
)
from helpers import get_image_sizes, startup_database, batch_generator
from flows import flow_insert_all_from_albums


# def add_recently_played(sp: spotipy.Spotify):
#     """
#     Queries Spotify for the user's recently played tracks and inserts them into the database.
#     """
#     logger.info("Querying recently played tracks from Spotify")
#     recently_played = sp.current_user_recently_played(limit=50)

#     for track in recently_played.get("items", []):
#         # First thing is to check if album is already in the database
#         album_id = track.get("track", {}).get("album", {}).get("id")
#         if not album_id:
#             logger.error(
#                 f"Failed to get album from track {track.get('track', {}).get('id')}"
#             )
#             continue

#         # If album doesn't exist I will add everything: Album, Artists, Genres,
#         # Tracks (from album)
#         if not get_object_by_id(album_id, "albums"):
#             insert_flow_from_album(album_id, sp)

#         # Now I can insert the streaming history since I know I have
#         # the track in the database.
#         track_id = track.get("track", {}).get("id")

#         if is_streaming_history_added(track.get("played_at"), track_id):
#             continue

#         try:
#             logger.info(
#                 f"Inserting streaming history for track {track_id} at {track.get('played_at')}"
#             )
#             insert_streaming_history(
#                 track.get("played_at"),
#                 track.get("track", {}).get("duration_ms"),
#                 track_id,
#                 track.get("context", {}).get("type"),
#                 # The rest here is always None when coming from recently played
#                 None,
#                 None,
#                 None,
#                 None,
#             )
#         except Exception as e:
#             logger.error(
#                 f"Failed to insert streaming history for track {track_id}: {e}"
#             )


def load_extended_history(dir: str):
    """
    Load all *.json inside a directory into a single list of dictionaries.
    """
    data = []

    for filename in os.listdir(dir):
        if filename.endswith(".json"):
            with open(os.path.join(dir, filename)) as f:
                data.extend(json.load(f))

    return data


def add_extended_history(sp: spotipy.Spotify):
    extended_history = load_extended_history("extended_history")
    logger.info(
        f"Loaded {len(extended_history)} items from extended history, adding to database. This may take a while."
    )

    print("NOT IMPLEMENTED, CONTINUE FROM HERE")
    for batch in batch_generator(extended_history, 50):
        pass

    # TODO: Here I need to do something like this...
    # Separate it in batches
    # Get the unique track_ids in that batch
    # Get only the track ids that are not in the database
    # Request their album ids and then send to the flow
    # After they are all added I can add the streaming history to the db
    #
    # The problem is that:
    # - A batch might have some podcasts so the batch will not actually have 50 tracks
    # - The batch might have a bunch of songs from the same album so I'm not actually
    # doing 50 requests...
    #
    # Is there a way to make sure I'm doing 50 requests every time?
    # Could I batch them in a way to guarantee that I have 50 tracks that are not in the db?
    # I really have to see what I prefer doing here, making the code complicated
    # or just making more requests than necessary...

    # batches = batch_generator(extended_history, 50)
    # for batch in batches:
    #     insert_flow_from_extended_history(batch, sp)
    # for data in extended_history:
    #     insert_flow_from_extended_history(data, sp)


def main():
    try:
        startup_database()
    except Exception as e:
        logger.fatal(f"Failed to start database: {e}")
        exit(1)

    # parser = argparse.ArgumentParser(
    #     description="CLI tool for Spotify data management."
    # )

    # parser.add_argument(
    #     "--recently-played",
    #     action="store_true",
    #     help="Fetch recently played tracks",
    # )
    # parser.add_argument(
    #     "--extended-history",
    #     action="store_true",
    #     help="Load extended streaming history, takes a while",
    # )

    album_ids = [
        "7fYdNpNuVdmdV5zYA0jvVp",
        "48bhYKY2DA7b0awsNe99Jd",
        "49NVSiUXtHUrWG46r4cnCS",
        "0falRoEbZAuDn4lUoUzjmy",
        "4yURApEmWq3Apn9zpjD6HN",
        "3xTvTulNR8Ba1uk0oDaQbs",
        "50nRFfP7eymMb2rfSffMr9",
        "4F2ApYDxzFRvN4XN2NNAYX",
        "1lzXKC7YtD8taNdv84K54L",
        "5EN0XQp11GkfhqKHJhmti0",
        "4izHHUUMnDtA8Uk70rRMPD",
    ]

    scope = "user-read-recently-played"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    flow_insert_all_from_albums(album_ids, sp)

    # # Parse the arguments
    # args = parser.parse_args()

    # # If nothing is passed, print help
    # if not any(vars(args).values()):
    #     parser.print_help()
    #     exit(1)

    # if args.extended_history or args.recently_played:
    #     # Log that it started
    #     logger.info("Starting...")

    #     if args.extended_history:
    #         add_extended_history(sp)

    #     if args.recently_played:
    #         add_recently_played(sp)

    #     logger.info("Finished")

    # Close the database connection
    close_connection()


if __name__ == "__main__":
    main()
