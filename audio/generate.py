import os
import json
from mutagen import File

AUDIO_ROOT = "."
SONGS_PATH = "songs.json"

def get_metadata(filepath):
    audio = File(filepath, easy=True)
    if not audio:
        return {"title": None, "year": None, "artists": []}
    title = audio.get("title", [None])[0]
    year_raw = audio.get("date", [None])[0] or audio.get("year", [None])[0]
    year = None
    if year_raw:
        if len(year_raw) >= 4 and year_raw[:4].isdigit():
            year = int(year_raw[:4])
    artists = audio.get("artist", [""])
    if artists:
        artists = [a.strip() for a in artists[0].replace(";", ",").split(",") if a.strip()]
    return {"title": title, "year": year, "artists": artists}

def load_songs():
    if os.path.exists(SONGS_PATH):
        with open(SONGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_songs(songs):
    with open(SONGS_PATH, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

def scan_audio_files():
    songs = load_songs()
    existing_files = set(songs.keys())

    for root, dirs, files in os.walk(AUDIO_ROOT):
        for file in files:
            if file.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg', '.wav')):
                filepath = os.path.join(root, file)
                relative_path = os.path.relpath(filepath, AUDIO_ROOT).replace("\\", "/")
                # Remove file extension from key to match existing format
                key_path = os.path.splitext(relative_path)[0]

                if key_path not in existing_files:
                    print(f"Processing new file: {relative_path}")
                    metadata = get_metadata(filepath)

                    # Create song entry
                    song = {
                        "title": [True, metadata["title"] or "Unknown Title"],
                        "sources": [[True, artist] for artist in metadata["artists"]] if metadata["artists"] else [[True, "Unknown Artist"]],
                        "audioFile": relative_path,
                        "startTime": None,
                        "endTime": None,
                        "level": None,
                        "year": metadata["year"]
                    }

                    songs[key_path] = song

    save_songs(songs)
    print(f"Total songs: {len(songs)}")

if __name__ == "__main__":
    scan_audio_files()