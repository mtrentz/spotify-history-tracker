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
from helpers import get_image_sizes, startup_database, get_date_based_on_precision


def search_and_insert_artist(artist_id: str, sp: spotipy.Spotify) -> str:
    """
    Queries Spotify for an artist and inserts it into the database.
    """
    logger.info(f"Querying artist {artist_id} from Spotify")
    artist = sp.artist(artist_id)

    image_sm, image_md, image_lg = get_image_sizes(artist.get("images", []))
    try:
        logger.info(f"Inserting artist {artist_id} into the database")
        insert_artist(
            artist_id,
            artist.get("name"),
            artist.get("popularity"),
            artist.get("followers", {}).get("total"),
            image_sm,
            image_md,
            image_lg,
        )
    except Exception as e:
        logger.error(f"Failed to insert artist {artist_id}: {e}")
        return None

    artist_genres = artist.get("genres", [])
    for genre in artist_genres:
        # Check if genre is already in the database
        artist_genre_id = get_genre_id(genre)
        if not artist_genre_id:
            try:
                logger.info(f"Inserting genre {genre} into the database")
                artist_genre_id = insert_genre(genre)
            except Exception as e:
                logger.error(f"Failed to insert genre {genre}: {e}")
                continue
        try:
            logger.info(
                f"Inserting artist_genre {artist_id}, {artist_genre_id} into the database"
            )
            insert_artist_genre(artist_id, artist_genre_id)
        except Exception as e:
            logger.error(
                f"Failed to insert artist_genre {artist_id}, {artist_genre_id}: {e}"
            )
            continue

    return artist_id


def insert_track_list(tracks: list, album_id: str, sp: spotipy.Spotify):
    for track in tracks:
        # Here I need to get all artists from the track
        # as there is a chance they are not in the database yet as they
        # could be different from album's artists (feats, etc)
        track_artist_ids = track.get("artists", [])
        track_artist_ids = [artist.get("id") for artist in track_artist_ids]

        for album_artist_id in track_artist_ids:
            if get_object_by_id(album_artist_id, "artists"):
                continue
            search_and_insert_artist(album_artist_id, sp)

        try:
            logger.info(f"Inserting track {track.get('id')} into the database")
            insert_track(
                track.get("id"),
                track.get("name"),
                track.get("disc_number"),
                track.get("duration_ms"),
                track.get("explicit"),
                # Popularity will never be present when track comes from album
                track.get("popularity"),
                track.get("track_number"),
                track.get("is_local"),
                album_id,
                track_artist_ids[0],
            )
        except Exception as e:
            logger.error(f"Failed to insert track {track.get('id')}: {e}")

        for track_artist_id in track_artist_ids:
            try:
                logger.info(
                    f"Inserting track_artist {track.get('id')}, {track_artist_id} into the database"
                )
                insert_track_artist(track.get("id"), track_artist_id)
            except Exception as e:
                logger.error(
                    f"Failed to insert track_artist {track.get('id')}, {track_artist_id}: {e}"
                )


def insert_flow_from_album(album_id: str, sp: spotipy.Spotify):
    """
    Assuming the album is not in the database, this function will
    query Spotify for the album and insert it into the database.

    It will also insert all artists, genres and tracks related to the album.
    """
    logger.info(f"Querying album {album_id} from Spotify")
    album = sp.album(album_id)

    # ARTISTS
    album_artist_ids = album.get("artists", [])
    album_artist_ids = [artist.get("id") for artist in album_artist_ids]

    for album_artist_id in album_artist_ids:
        if get_object_by_id(album_artist_id, "artists"):
            continue

        search_and_insert_artist(album_artist_id, sp)

    # ALBUM
    image_sm, image_md, image_lg = get_image_sizes(album.get("images", []))
    try:
        logger.info(f"Inserting album {album_id} into the database")
        insert_album(
            album_id,
            album.get("name"),
            album.get("label"),
            album.get("popularity"),
            get_date_based_on_precision(
                album.get("release_date_precision"), album.get("release_date")
            ),
            album.get("total_tracks"),
            image_sm,
            image_md,
            image_lg,
            album_artist_ids[0],
        )
    except Exception as e:
        logger.error(f"Failed to insert album {album_id}: {e}")
        raise e

    for album_artist_id in album_artist_ids:
        try:
            logger.info(
                f"Inserting album_artist {album_id}, {album_artist_id} into the database"
            )
            insert_album_artist(album_id, album_artist_id)
        except Exception as e:
            logger.error(
                f"Failed to insert album_artist {album_id}, {album_artist_id}: {e}"
            )
            continue

    album_genres = album.get("genres", [])
    for genre in album_genres:
        # Check if genre is already in the database
        album_genre_id = get_genre_id(genre)
        if not album_genre_id:
            try:
                logger.info(f"Inserting genre {genre} into the database")
                album_genre_id = insert_genre(genre)
            except Exception as e:
                logger.error(f"Failed to insert genre {genre}: {e}")
                continue
        try:
            logger.info(
                f"Inserting album_genre {album_id}, {album_genre_id} into the database"
            )
            insert_album_genre(album_id, album_genre_id)
        except Exception as e:
            logger.error(
                f"Failed to insert album_genre {album_id}, {album_genre_id}: {e}"
            )
            continue

    # TRACKS
    tracks = album.get("tracks", {})
    insert_track_list(tracks.get("items", []), album_id, sp)

    # Some albums have more than 50 tracks, if this is the case
    # I will query the next 50 tracks and insert them as well.
    while tracks.get("next"):
        logger.info(f"Querying next 50 tracks from album {album_id} from Spotify")
        tracks = sp.next(tracks)
        insert_track_list(tracks.get("items", []), album_id, sp)


def insert_flow_from_track(track_id: str, sp: spotipy.Spotify):
    """
    Assuming the track is not in the database, this function will
    query Spotify for the track, get its album and run the insert_flow_from_album
    """
    logger.info(f"Querying track {track_id} from Spotify")
    track = sp.track(track_id)
    album_id = track.get("album", {}).get("id")

    if not album_id:
        logger.error(f"Failed to get album from track {track_id}")
        return

    insert_flow_from_album(album_id, sp)


def insert_flow_from_extended_history(data: dict, sp: spotipy.Spotify):
    """
    From a single object from the extended history I will insert everything
    into the database.

    Some extra fields that I will get here:
    - reason_start
    - reason_end
    - skipped
    - shuffle
    """
    # If not spotify_track_uri I will skip
    # This could mean it's a podcast or something else!
    if not data.get("spotify_track_uri"):
        logger.warning(f"Failed to get spotify_track_uri from data as {data.get('ts')}")
        return

    track_id = data.get("spotify_track_uri").replace("spotify:track:", "")

    # If track doesn't exist I will do the full flow
    if not get_object_by_id(track_id, "tracks"):
        insert_flow_from_track(track_id, sp)

    # Now I can insert the streaming history since I know I have
    # the track in the database.
    if is_streaming_history_added(data.get("ts"), track_id):
        return

    try:
        logger.info(
            f"Inserting streaming history for track {track_id} at {data.get('ts')}"
        )
        # Here it simply adds nothing if there is already
        # a history at the same time for the same track
        insert_streaming_history(
            data.get("ts"),
            data.get("ms_played"),
            track_id,
            # Context is None when coming from extended history
            None,
            data.get("reason_start"),
            data.get("reason_end"),
            data.get("skipped"),
            data.get("shuffle"),
        )
    except Exception as e:
        logger.error(f"Failed to insert streaming history for track {track_id}: {e}")
        return


def add_recently_played(sp: spotipy.Spotify):
    """
    Queries Spotify for the user's recently played tracks and inserts them into the database.
    """
    logger.info("Querying recently played tracks from Spotify")
    recently_played = sp.current_user_recently_played(limit=50)

    for track in recently_played.get("items", []):
        # First thing is to check if album is already in the database
        album_id = track.get("track", {}).get("album", {}).get("id")
        if not album_id:
            logger.error(
                f"Failed to get album from track {track.get('track', {}).get('id')}"
            )
            continue

        # If album doesn't exist I will add everything: Album, Artists, Genres,
        # Tracks (from album)
        if not get_object_by_id(album_id, "albums"):
            insert_flow_from_album(album_id, sp)

        # Now I can insert the streaming history since I know I have
        # the track in the database.
        track_id = track.get("track", {}).get("id")

        if is_streaming_history_added(track.get("played_at"), track_id):
            continue

        try:
            logger.info(
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
    for data in extended_history:
        insert_flow_from_extended_history(data, sp)


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
