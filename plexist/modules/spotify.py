import logging
from typing import List

import os

import spotipy
from plexapi.server import PlexServer

from .helperClasses import Playlist, Track, UserInputs
from .plex import update_or_create_plex_playlist


def _get_sp_user_playlists(
    sp: spotipy.Spotify, user_id: str, suffix: str = " - " + os.getenv("SPOTIFY_PLAYLIST_SUFFIX")
) -> List[Playlist]:
    playlists = []

    try:
        sp_playlists = sp.user_playlists(user_id)
        while sp_playlists:
            for playlist in sp_playlists["items"]:
                playlists.append(
                    Playlist(
                        id=playlist["uri"],
                        name=playlist["name"] + " - " + os.getenv("SPOTIFY_PLAYLIST_SUFFIX"),
                        description=playlist.get("description", ""),
                        poster=""
                        if len(playlist["images"]) == 0
                        else playlist["images"][0].get("url", ""),
                    )
                )
            if sp_playlists["next"]:
                sp_playlists = sp.next(sp_playlists)
            else:
                sp_playlists = None
    except:
        logging.error("Spotify User ID Error")
    return playlists


def _get_sp_tracks_from_playlist(
    sp: spotipy.Spotify, user_id: str, playlist: Playlist
) -> List[Track]:
    def extract_sp_track_metadata(track) -> Track:
        title = track["track"]["name"]
        artist = track["track"]["artists"][0]["name"]
        album = track["track"]["album"]["name"]
        url = track["track"]["external_urls"].get("spotify", "")
        year = ""  # Default value
        genre = ""  # Default value
        return Track(title, artist, album, url, year, genre)
    sp_playlist_tracks = sp.user_playlist_tracks(user_id, playlist.id)
    tracks = list(
        map(
            extract_sp_track_metadata,
            [i for i in sp_playlist_tracks["items"] if i.get("track")],
        )
    )
    while sp_playlist_tracks["next"]:
        sp_playlist_tracks = sp.next(sp_playlist_tracks)
        tracks.extend(
            list(
                map(
                    extract_sp_track_metadata,
                    [i for i in sp_playlist_tracks["items"] if i.get("track")],
                )
            )
        )
    return tracks

def spotify_playlist_sync(
    sp: spotipy.Spotify, plex: PlexServer, userInputs: UserInputs
) -> None:
    try:
        playlists = _get_sp_user_playlists(sp, userInputs.spotify_user_id)
        if playlists:
            for playlist in playlists:
                logging.info(f"Syncing playlist: {playlist.name}")
                tracks = _get_sp_tracks_from_playlist(
                    sp, userInputs.spotify_user_id, playlist
                )
                # Pass additional metadata like year and genre if available
                update_or_create_plex_playlist(plex, playlist, tracks, userInputs)
        else:
            logging.error("No Spotify playlists found for the user provided.")
    except spotipy.SpotifyException as e:
        logging.error(f"Spotify Exception: {e}")
