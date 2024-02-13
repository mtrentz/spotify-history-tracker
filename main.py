import os
import json
import spotipy
import argparse
from spotipy.oauth2 import SpotifyOAuth
from db import close_connection, query_db
from logger import logger
from models import (
    insert_streaming_history,
    get_object_by_id,
    is_streaming_history_added,
    get_new_ids,
)
from helpers import startup_database, batch_generator
from flows import flow_insert_all_from_albums, flow_insert_all_from_tracks
import time


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

    # First step is to make sure all songs were added to the database
    # So I will do an outer batch of 10 in 10 songs until I found 40-50 songs
    # that are not in the database.
    # Then I will request them all until I finished all extended history.
    outer_batch = []
    for inner_batch in batch_generator(extended_history, 10):
        ids = []
        for item in inner_batch:
            try:
                track_id = item.get("spotify_track_uri").replace("spotify:track:", "")
                ids.append(track_id)
            except Exception:
                logger.warning("Failed to get track id, likely a podcast.")
                continue

        outer_batch.extend(get_new_ids("tracks", ids))
        if len(outer_batch) >= 40:
            # Send to the flow
            flow_insert_all_from_tracks(outer_batch, sp)
            outer_batch = []
            # For good measure I will sleep a bit
            time.sleep(3)

    # Only now that I will go over the extended history and add the streaming history
    for data in extended_history:
        try:
            track_id = data.get("spotify_track_uri").replace("spotify:track:", "")
        except Exception:
            # This is just a podcast, I've logged about it above, here I just
            # ignore.
            continue

        if is_streaming_history_added(data.get("ts"), track_id):
            continue

        try:
            logger.debug(
                f"Inserting streaming history for track {track_id} at {data.get('ts')}"
            )
            insert_streaming_history(
                data.get("ts"),
                data.get("ms_played"),
                track_id,
                # Context is always None when coming from extended history
                None,
                data.get("reason_start"),
                data.get("reason_end"),
                data.get("skipped"),
                data.get("shuffle"),
            )
        except Exception as e:
            logger.warning(
                f"Failed to insert streaming history for track {track_id}. WILL TRY AGAIN: {e}"
            )
            # I will try again by actually inserting the track
            try:
                flow_insert_all_from_tracks([track_id], sp)
                insert_streaming_history(
                    data.get("ts"),
                    data.get("ms_played"),
                    track_id,
                    # Context is always None when coming from extended history
                    None,
                    data.get("reason_start"),
                    data.get("reason_end"),
                    data.get("skipped"),
                    data.get("shuffle"),
                )
            except Exception as e:
                logger.error(
                    f"Failed to insert streaming history for track {track_id} even after trying to insert it: {e}"
                )

    # Merge possible "duplicates" between the extended history and the recently played
    # Comments for this are in the fix_history_merge.sql file
    try:
        with open("fix_history_merge.sql") as f:
            query = f.read()
            query_db(query, commit=True)
    except Exception as e:
        logger.error(f"Failed to merge history: {e}")


def add_recently_played(sp: spotipy.Spotify):
    """
    Queries Spotify for the user's recently played tracks and inserts them into the database.
    """
    logger.info("Querying recently played tracks from Spotify")
    recently_played = sp.current_user_recently_played(limit=50)

    # Find all albums that are not in the database
    album_ids = set()

    for track in recently_played.get("items", []):
        album_id = track.get("track", {}).get("album", {}).get("id")
        if album_id and not get_object_by_id(album_id, "albums"):
            album_ids.add(album_id)

    # Insert all albums that are not in the database
    # Batch it becuause there is a chance of being more than 20
    for batch in batch_generator(list(album_ids), 20):
        flow_insert_all_from_albums(batch, sp)

    # Now I can insert the streaming history since I know I have
    # the track in the database.
    for track in recently_played.get("items", []):
        track_id = track.get("track", {}).get("id")

        if is_streaming_history_added(track.get("played_at"), track_id):
            continue

        try:
            logger.debug(
                f"Inserting streaming history for track {track_id} at {track.get('played_at')}"
            )
            insert_streaming_history(
                track.get("played_at"),
                track.get("track", {}).get("duration_ms"),
                track_id,
                track.get("context", {}).get("type"),
                # The rest here is always None when coming from recently played
                None,
                None,
                None,
                None,
            )
        except Exception as e:
            logger.error(
                f"Failed to insert streaming history for track {track_id}: {e}"
            )


def main():

    try:
        startup_database()
    except Exception as e:
        logger.fatal(f"Failed to start database: {e}")
        exit(1)

    parser = argparse.ArgumentParser(
        description="CLI tool for Spotify data management."
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for logging",
    )
    parser.add_argument(
        "--recently-played",
        action="store_true",
        help="Fetch recently played tracks",
    )
    parser.add_argument(
        "--extended-history",
        action="store_true",
        help="Load extended streaming history, takes a while",
    )

    scope = "user-read-recently-played"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

    # Parse the arguments
    args = parser.parse_args()

    # If nothing is passed, print help
    if not any(vars(args).values()):
        parser.print_help()
        exit(1)

    # Set the log level
    if args.debug:
        logger.setLevel("DEBUG")

    if args.extended_history or args.recently_played:
        # Log that it started
        logger.info("Starting...")

        if args.extended_history:
            add_extended_history(sp)

        if args.recently_played:
            add_recently_played(sp)

        logger.info("Finished")

    # Close the database connection
    close_connection()


if __name__ == "__main__":
    main()
