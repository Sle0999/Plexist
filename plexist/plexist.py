#!/usr/bin/env python3

import logging
import os
import time

import deezer
import spotipy
from plexapi.server import PlexServer
from spotipy.oauth2 import SpotifyClientCredentials

from modules.deezer import deezer_playlist_sync
from modules.helperClasses import UserInputs
from modules.spotify import spotify_playlist_sync
from modules.plex import initialize_db  # Importing the database initialization function


def read_environment_variables():
    return UserInputs(
        plex_url=os.getenv("PLEX_URL"),
        plex_token=os.getenv("PLEX_TOKEN"),
        write_missing_as_csv=os.getenv("WRITE_MISSING_AS_CSV", "0") == "1",
        add_playlist_poster=os.getenv("ADD_PLAYLIST_POSTER", "1") == "1",
        add_playlist_description=os.getenv("ADD_PLAYLIST_DESCRIPTION", "1") == "1",
        append_instead_of_sync=os.getenv("APPEND_INSTEAD_OF_SYNC", "False") == "1",
        wait_seconds=int(os.getenv("SECONDS_TO_WAIT", 86400)),
        spotipy_client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        spotipy_client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        spotify_user_id=os.getenv("SPOTIFY_USER_ID"),
        spotify_playlist_suffix=os.getenv("SPOTIFY_PLAYLIST_SUFFIX"),
        deezer_user_id=os.getenv("DEEZER_USER_ID"),
        deezer_playlist_ids=os.getenv("DEEZER_PLAYLIST_ID"),
    )



def initialize_plex_server(user_inputs):
    if user_inputs.plex_url and user_inputs.plex_token:
        try:
            return PlexServer(user_inputs.plex_url, user_inputs.plex_token)
        except Exception as e:
            logging.error(f"Plex Authorization error: {e}")
            return None
    else:
        logging.error("Missing Plex Authorization Variables")
        return None


def initialize_spotify_client(user_inputs):
    if (
        user_inputs.spotipy_client_id
        and user_inputs.spotipy_client_secret
        and user_inputs.spotify_user_id
    ):
        try:
            return spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    user_inputs.spotipy_client_id,
                    user_inputs.spotipy_client_secret,
                )
            )
        except Exception as e:
            logging.error(f"Spotify Authorization error: {e}")
            return None
    else:
        logging.error("Missing one or more Spotify Authorization Variables")
        return None


def main():
    initialize_db()  # Initialize the database at the start of the main function

    user_inputs = read_environment_variables()
    plex = initialize_plex_server(user_inputs)

    if plex is None:
        return

    while True:
        logging.info("Starting playlist sync")

        # Spotify sync
        logging.info("Starting Spotify playlist sync")
        sp = initialize_spotify_client(user_inputs)
        if sp is not None:
            spotify_playlist_sync(sp, plex, user_inputs)
            logging.info("Spotify playlist sync complete")
        else:
            logging.error("Spotify sync skipped due to authorization error")

        # Deezer sync
        logging.info("Starting Deezer playlist sync")
        dz = deezer.Client()
        deezer_playlist_sync(dz, plex, user_inputs)
        logging.info("Deezer playlist sync complete")

        logging.info("All playlist(s) sync complete")
        logging.info(f"Sleeping for {user_inputs.wait_seconds} seconds")

        time.sleep(user_inputs.wait_seconds)


if __name__ == "__main__":
    main()
