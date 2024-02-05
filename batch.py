from spotipy.oauth2 import SpotifyOAuth
import spotipy
from dotenv import load_dotenv

load_dotenv()

scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


# # Around 10 valid ids
# track_ids = [
#     "2dJwnskDT5AHUso6o1Acnp",
#     "3xGJuHvSxFJxxYlHj5BIoT",
#     "1hHCV2J3JUfogmm1IxA3Ow",
#     "19aYH2zhbnTNx4plfenrIk",
#     "7kQn6wJR2WVXJWQeY2c8i7",
#     "42y4SiykF2qUeoICoVg03s",
#     "23wy01AlGPVFGjJtUqs8Ji",
#     "3HTDOoRoGvwpmMTIOOQehV",
#     "76ExGgO2njBAqvPAeh1x4",
#     "4Vcw9SLn0t0EsHaKvy7tWq",
#     "1aavevgQdmNMbbUqiptqD9",
#     "02pf9lLM8Nb8l4u4ts1GWb",
#     "3mTqSxuMTeeAkIl6nrXkr6",
#     "44sw25l5s3dUQx38QQ4hix",
#     "4nWn9o7NTpuqzHQ5hyae8U",
#     "05f8Hg3RSfiPSCBQOtxl3i",
#     "6lDo13SSgTv0WbyUQKgnjk",
#     "3OcBH9Vzd1UwJkQd3r1dVG",
#     "383QXk8nb2YrARMUwDdjQS",
#     "6HZILIRieu8S0iqY8kIKhj",
#     "4EAV2cKiqKP5UPZmY6dejk",
#     "439xDVYKceMIrSkrzgYAoX",
#     "17bgialGAwoiGj1STY4cnR",
# ]

# # Batch request
# resp = sp.tracks(track_ids)

# # Print the song names
# for track in resp["tracks"]:
#     print(track["name"])

# # Dump the response
import json

# with open("batch_response.json", "w") as f:
#     json.dump(resp, f)


# 10 album ids
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

# Batch request
resp = sp.albums(album_ids)

# Save to json
with open("batch_album_response.json", "w") as f:
    json.dump(resp, f)
