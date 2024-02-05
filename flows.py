import spotipy
from typing import List, Dict, Any
from logger import logger
from helpers import get_image_sizes, batch_generator, get_date_based_on_precision
from models import (
    insert_artist,
    insert_genre,
    insert_artist_genre,
    get_genre_id,
    insert_album,
    insert_album_genre,
    get_object_by_id,
    insert_track,
    insert_track_artist,
)


def insert_track_list(tracks: list, album_id: str, sp: spotipy.Spotify):
    """
    In most cases this function won't call the Spotify API.

    If there are tracks in side the album from an artist that is not in the
    database then calls will be made. This will happens for track feats, etc.

    It just adds the list of all tracks of an album to the database.
    """

    # There is a chance that some artists are not in the database yet
    # if the tracks have feats. I will loop through all tracks and get all
    # artists from them and insert them in the database.
    new_artists = set()

    for track in tracks:
        track_artist_ids = track.get("artists", [])
        track_artist_ids = [artist.get("id") for artist in track_artist_ids]

        for album_artist_id in track_artist_ids:
            if not get_object_by_id(album_artist_id, "artists"):
                new_artists.add(album_artist_id)

    if new_artists:
        for batch in batch_generator(list(new_artists), 50):
            search_and_insert_artists(batch, sp)

    # Now I can be sure that all artists are in the database so I can
    # insert the tracks!
    for track in tracks:
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
                track.get("artists", [{"id": None}])[0].get("id"),
            )
        except Exception as e:
            logger.error(f"Failed to insert track {track.get('id')}: {e}")

        track_artist_ids = track.get("artists", [])
        track_artist_ids = [artist.get("id") for artist in track_artist_ids]

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


def search_and_insert_artists(
    artist_ids: List[str], sp: spotipy.Spotify
) -> List[Dict[str, Any]]:
    """
    Adds all artists to the database.

    Requests up to 50 artists from spotify and insert them in the database.
    """
    if len(artist_ids) > 50:
        # Log warning
        logger.warning("Too many artists to request at once. Requesting only 50.")
        artist_ids = artist_ids[:50]

    # Request all artists
    logger.info(f"Querying {len(artist_ids)} artists from Spotify")
    artists = sp.artists(artist_ids)

    # Insert all artists
    for artist in artists.get("artists", []):
        # Get image sizes
        image_sm, image_md, image_lg = get_image_sizes(artist.get("images", []))
        try:
            logger.info(f"Inserting artist {artist.get('id')} into the database")
            insert_artist(
                artist.get("id"),
                artist.get("name"),
                artist.get("popularity"),
                artist.get("followers", {}).get("total"),
                image_sm,
                image_md,
                image_lg,
            )
        except Exception as e:
            logger.error(
                f"Failed to insert artist {artist.get('id')} into the database: {e}"
            )
            continue

        # Genres
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
                    f"Inserting artist_genre {artist.get('id')}, {artist_genre_id} into the database"
                )
                insert_artist_genre(artist.get("id"), artist_genre_id)
            except Exception as e:
                logger.error(
                    f"Failed to insert artist_genre {artist.get('id')}, {artist_genre_id}: {e}"
                )
                continue


def flow_insert_all_from_albums(
    album_ids: List[str], sp: spotipy.Spotify
) -> List[Dict[str, Any]]:
    """
    Adds all albums, tracks and artists to the database.

    Requests up to 20 albums and their artists from spotify
    and insert everything in the database.

    Information related to tracks comes from the album response.

    """
    if len(album_ids) > 20:
        # Log warning
        logger.warning("Too many albums to request at once. Requesting only 20.")
        album_ids = album_ids[:20]

    # Request all albums
    logger.info(f"Querying {len(album_ids)} albums from Spotify")
    albums = sp.albums(album_ids)

    # Get all artists
    artist_ids = set()

    for album in albums.get("albums", []):
        for artist in album.get("artists", [{"id": None}]):
            artist_ids.add(artist.get("id"))

    # Now request and insert all artists in batches
    for batch in batch_generator(list(artist_ids), 50):
        search_and_insert_artists(batch, sp)

        # Now I know for sure that all artists are in the database
        # so I can insert the albums!
        for album in albums.get("albums", []):
            # Get image sizes
            image_sm, image_md, image_lg = get_image_sizes(album.get("images", []))
            try:
                logger.info(f"Inserting album {album.get('id')} into the database")
                insert_album(
                    album.get("id"),
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
                    album.get("artists", [{"id": None}])[0].get("id"),
                )
            except Exception as e:
                logger.error(
                    f"Failed to insert album {album.get('id')} into the database: {e}"
                )
                continue

            # Genres
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
                        f"Inserting album_genre {album.get('id')}, {album_genre_id} into the database"
                    )
                    insert_album_genre(album.get("id"), album_genre_id)
                except Exception as e:
                    logger.error(
                        f"Failed to insert album_genre {album.get('id')}, {album_genre_id}: {e}"
                    )
                    continue

    # Finally add all tracks from all albums to the database.
    # These comes from the album response and no extra requests are needed!
    for album in albums.get("albums", []):
        tracks = album.get("tracks", {})
        insert_track_list(tracks.get("items", []), album.get("id"), sp)

        # Some albums have more than 50 tracks, if this is the case
        # I will query the next 50 tracks and insert them as well.
        while tracks.get("next"):
            logger.info(f"Querying next 50 tracks from album {album.get('id')}")
            tracks = sp.next(tracks)
            insert_track_list(tracks.get("items", []), album.get("id"), sp)


def flow_insert_all_from_tracks(
    track_ids: List[str], sp: spotipy.Spotify
) -> List[Dict[str, Any]]:
    """
    This function starts from a list of up to 50 track_ids and requests all tracks
    with the intent of getting their album ids.

    Having the album ids it will run the flow_insert_all_from_albums to insert
    everything else.
    """
    if len(track_ids) > 50:
        # Log warning
        logger.warning("Too many tracks to request at once. Requesting only 50.")
        track_ids = track_ids[:50]

    # Request all tracks
    logger.info(f"Querying {len(track_ids)} tracks from Spotify")
    tracks = sp.tracks(track_ids)

    # Get all album ids
    album_ids = set()
    for track in tracks.get("tracks", []):
        album_ids.add(track.get("album", {}).get("id"))

    # Now request and insert all albums in batches
    for batch in batch_generator(list(album_ids), 20):
        flow_insert_all_from_albums(batch, sp)
