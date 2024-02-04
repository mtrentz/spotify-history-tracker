CREATE TABLE IF NOT EXISTS genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS artists (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    popularity INTEGER,
    followers INTEGER,
    image_sm TEXT,
    image_md TEXT,
    image_lg TEXT
);

CREATE TABLE IF NOT EXISTS albums (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    label VARCHAR(255),
    popularity INTEGER,
    release_date DATE,
    total_tracks INTEGER,
    image_sm TEXT,
    image_md TEXT,
    image_lg TEXT,
    main_artist_id VARCHAR(255) REFERENCES artists(id)
);

CREATE TABLE IF NOT EXISTS tracks (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    disc_number INTEGER,
    duration INTEGER,
    is_explicit BOOLEAN,
    popularity INTEGER,
    track_number INTEGER,
    is_local BOOLEAN,
    album_id VARCHAR(255) REFERENCES albums(id),
    main_artist_id VARCHAR(255) REFERENCES artists(id)
);

CREATE TABLE IF NOT EXISTS streaming_history (
    played_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    ms_played INTEGER,
    track_id VARCHAR(255) NOT NULL REFERENCES tracks(id),
    context TEXT,
    reason_start TEXT,
    reason_end TEXT,
    skipped BOOLEAN,
    shuffle BOOLEAN,
    PRIMARY KEY (played_at, track_id)
);

CREATE TABLE IF NOT EXISTS album_artists (
    album_id VARCHAR(255) REFERENCES albums(id),
    artist_id VARCHAR(255) REFERENCES artists(id),
    PRIMARY KEY (album_id, artist_id)
);

CREATE TABLE IF NOT EXISTS track_artists (
    track_id VARCHAR(255) REFERENCES tracks(id),
    artist_id VARCHAR(255) REFERENCES artists(id),
    PRIMARY KEY (track_id, artist_id)
);

CREATE TABLE IF NOT EXISTS album_genres (
    album_id VARCHAR(255) REFERENCES albums(id),
    genre_id INT REFERENCES genres(id),
    PRIMARY KEY (album_id, genre_id)
);

CREATE TABLE IF NOT EXISTS artist_genres (
    artist_id VARCHAR(255) REFERENCES artists(id),
    genre_id INT REFERENCES genres(id),
    PRIMARY KEY (artist_id, genre_id)
);