from db import query_db
from typing import Optional, Union


def insert_artist(
    artist_id: str,
    artist_name: str,
    popularity: Optional[int],
    followers: Optional[int],
    image_sm: Optional[str],
    image_md: Optional[str],
    image_lg: Optional[str],
):
    """
    Inserts an artist into the database.
    """
    query = """
    INSERT INTO artists (id, name, popularity, followers, image_sm, image_md, image_lg)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING
    """
    query_db(
        query,
        (artist_id, artist_name, popularity, followers, image_sm, image_md, image_lg),
        commit=True,
    )


def insert_album(
    album_id: str,
    name: str,
    label: Optional[str],
    popularity: Optional[int],
    release_date: Optional[str],
    total_tracks: int,
    image_sm: Optional[str],
    image_md: Optional[str],
    image_lg: Optional[str],
    main_artist_id: str,
):
    """
    Inserts an album into the database.
    """
    query = """
    INSERT INTO albums (id, name, label, popularity, release_date, total_tracks, image_sm, image_md, image_lg, main_artist_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING
    """
    query_db(
        query,
        (
            album_id,
            name,
            label,
            popularity,
            release_date,
            total_tracks,
            image_sm,
            image_md,
            image_lg,
            main_artist_id,
        ),
        commit=True,
    )


def insert_track(
    track_id: str,
    name: str,
    disc_number: int,
    duration: int,
    is_explicit: bool,
    popularity: Optional[int],
    track_number: int,
    is_local: bool,
    album_id: str,
    main_artist_id: str,
):
    """
    Inserts a track into the database.
    """
    query = """
    INSERT INTO tracks (id, name, disc_number, duration, is_explicit, popularity, track_number, is_local, album_id, main_artist_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO NOTHING
    """
    query_db(
        query,
        (
            track_id,
            name,
            disc_number,
            duration,
            is_explicit,
            popularity,
            track_number,
            is_local,
            album_id,
            main_artist_id,
        ),
        commit=True,
    )


def insert_album_artist(album_id: str, artist_id: str):
    """
    Inserts an artist association for an album into the database.
    """
    query = """
    INSERT INTO album_artists (album_id, artist_id)
    VALUES (%s, %s)
    ON CONFLICT (album_id, artist_id) DO NOTHING
    """
    query_db(query, (album_id, artist_id), commit=True)


def insert_track_artist(track_id: str, artist_id: str):
    """
    Inserts an artist association for a track into the database.
    """
    query = """
    INSERT INTO track_artists (track_id, artist_id)
    VALUES (%s, %s)
    ON CONFLICT (track_id, artist_id) DO NOTHING
    """
    query_db(query, (track_id, artist_id), commit=True)


def insert_streaming_history(
    played_at: str,
    ms_played: int,
    track_id: str,
    context: Optional[str],
    reason_start: Optional[str],
    reason_end: Optional[str],
    skipped: Optional[bool],
    shuffle: Optional[bool],
):
    """
    Inserts a streaming history record into the database.
    """
    query = """
    INSERT INTO
        streaming_history (played_at, ms_played, track_id, context, reason_start, reason_end, skipped, shuffle)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (played_at, track_id) DO NOTHING
    """
    query_db(
        query,
        (
            played_at,
            ms_played,
            track_id,
            context,
            reason_start,
            reason_end,
            skipped,
            shuffle,
        ),
        commit=True,
    )


def insert_genre(name: str) -> int:
    """
    Inserts a genre into the database and returns its ID.
    """
    query = """
    INSERT INTO genres (name)
    VALUES (%s)
    ON CONFLICT (name) DO NOTHING
    RETURNING id
    """
    genre_id = query_db(query, (name,), commit=True, fetchall=True)
    return genre_id[0][0] if genre_id else None


def insert_artist_genre(artist_id: str, genre_id: int):
    """
    Inserts a genre association for an artist into the database.
    """
    query = """
    INSERT INTO artist_genres (artist_id, genre_id)
    VALUES (%s, %s)
    ON CONFLICT (artist_id, genre_id) DO NOTHING
    """
    query_db(query, (artist_id, genre_id), commit=True)


def insert_album_genre(album_id: str, genre_id: int):
    """
    Inserts a genre association for an album into the database.
    """
    query = """
    INSERT INTO album_genres (album_id, genre_id)
    VALUES (%s, %s)
    ON CONFLICT (album_id, genre_id) DO NOTHING
    """
    query_db(query, (album_id, genre_id), commit=True)


def get_object_by_id(id: str, table: str) -> Union[str, int, None]:
    """
    Get an object from the database by id
    """
    query = f"""
    SELECT id FROM {table} WHERE id = %s
    """
    result = query_db(query, (id,), fetchall=True)
    return result[0][0] if result else None


def get_genre_id(name: str) -> Union[int, None]:
    """
    Get a genre ID from the database by name
    """
    query = """
    SELECT id FROM genres WHERE name = %s
    """
    result = query_db(query, (name,), fetchall=True)
    return result[0][0] if result else None


def is_streaming_history_added(played_at: str, track_id: str) -> bool:
    """
    Check if a streaming history record is already added
    """
    query = """
    SELECT played_at FROM streaming_history WHERE played_at = %s AND track_id = %s
    """
    result = query_db(query, (played_at, track_id), fetchall=True)
    return bool(result)


def get_new_ids(table: str, ids: list) -> list:
    """
    From a list of IDs, return the ones that are not in the database
    """
    query = f"""
        SELECT t.id
        FROM unnest(%s::text[]) AS t(id)
        LEFT JOIN {table} ON {table}.id = t.id
        WHERE {table}.id IS NULL
    """
    result = query_db(query, (ids,), fetchall=True)
    results = [r[0] for r in result]
    return results
