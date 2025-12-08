# netlify deploy --dir collections --prod
import os
import json
from mutagen import File

AUDIO_ROOT = "."
COLLECTIONS_PATH = "data.json"

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

def load_collections():
    if os.path.exists(COLLECTIONS_PATH):
        with open(COLLECTIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Migrate old "title" to "titles"
        for i, collection in enumerate(data.get("collections", [])):
            for song in collection.get("songs", []):
                if "title" in song and "titles" not in song:
                    song["titles"] = [[True, song["title"]]]
                    del song["title"]
                # Migrate titles to new format if they are strings
                if "titles" in song and song["titles"]:
                    if not isinstance(song["titles"][0], list):
                        song["titles"] = [[True, title] for title in song["titles"]]
            # Set defaults for collection fields
            collection.setdefault("title", None)
            collection.setdefault("description", None)
            collection.setdefault("difficulty", None)
            collection.setdefault("gameStyle", 1)
            collection.setdefault("disabledLifelines", [])
            collection.setdefault("sourceName", None)
            collection.setdefault("author", None)
            collection.setdefault("covers", [])
            # Migrate old guessSongOnly to gameStyle
            if "guessSongOnly" in collection:
                collection["gameStyle"] = 3 if collection["guessSongOnly"] else 1
                del collection["guessSongOnly"]
            # Set defaults for song fields
            for song in collection.get("songs", []):
                # Migrate artists to sources
                if "artists" in song and "sources" not in song:
                    song["sources"] = [[True, artist] for artist in song["artists"]]
                    del song["artists"]
                song.setdefault("sources", [])
                song.setdefault("titles", [])
                song.setdefault("audioFile", "")
                song.setdefault("startTime", None)
                song.setdefault("year", None)
            # Reorder collection keys to ensure "songs" is last
            reordered = dict((k, collection[k]) for k in ["id", "title", "description", "difficulty", "gameStyle", "disabledLifelines", "sourceName", "author", "covers", "songs"])
            data["collections"][i] = reordered
        return data.get("collections", [])
    return []

def save_collections(collections):
    with open(COLLECTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump({"collections": collections}, f, indent="\t", ensure_ascii=False)

def main():
    existing = {c["id"] for c in load_collections()}
    collections = load_collections()
    for folder in os.listdir(AUDIO_ROOT):
        folder_path = os.path.join(AUDIO_ROOT, folder)
        if not os.path.isdir(folder_path) or folder.startswith('.'):
            continue
        songs = []
        for root, dirs, files in os.walk(folder_path):
            for fname in files:
                if not fname.lower().endswith((".mp3", ".flac", ".wav", ".ogg", ".m4a")):
                    continue
                fpath = os.path.join(root, fname)
                meta = get_metadata(fpath)
                songs.append({
                    "titles": [[True, meta["title"]]] if meta["title"] else [],
                    "sources": [[True, artist] for artist in meta["artists"]],
                    "audioFile": fpath.replace("\\", "/"),
                    "startTime": None,
                    "year": meta["year"]
                })
        if songs:  # Only add if there are songs
            songs.sort(key=lambda s: s.get("year") or 0, reverse=True)
            collection_data = {
                "id": folder,
                "title": None,
                "description": None,
                "difficulty": None,
                "gameStyle": 1,
                "disabledLifelines": [],
                "sourceName": None,
                "author": None,
                "covers": [],
                "songs": songs
            }
            if folder in existing:
                # Update existing
                for i, c in enumerate(collections):
                    if c["id"] == folder:
                        # Preserve existing metadata
                        collection_data["title"] = c.get("title")
                        collection_data["description"] = c.get("description")
                        collection_data["difficulty"] = c.get("difficulty")
                        collection_data["gameStyle"] = c.get("gameStyle", 1)
                        collection_data["disabledLifelines"] = c.get("disabledLifelines", [])
                        collection_data["sourceName"] = c.get("sourceName")
                        collection_data["author"] = c.get("author")
                        collection_data["covers"] = c.get("covers", [])
                        # Merge songs: keep existing and add new ones not already present
                        existing_songs = c["songs"]
                        for new_song in songs:
                            if not any(s.get("audioFile") == new_song["audioFile"] for s in existing_songs):
                                existing_songs.append(new_song)
                        collection_data["songs"] = existing_songs
                        collections[i] = collection_data
                        break
            else:
                collections.append(collection_data)
    save_collections(collections)

if __name__ == "__main__":
    main()