# -- Imports -- #
from classes import *
import json

# -- Function -- #
def load_albums() -> Manager:
    with open("albums.json", "r") as file:
        load_data: list[dict] = json.load(file)
        data = Manager()

        for instance in load_data:
            album = Album(**instance)
            data.add(album)

    return data

def create_poll_data(data: Manager) -> dict[str, Album]:
    return {str(album): album for album in data.albums}

def save_data(data: Manager) -> None:
    album_data = [album.__dict__ for album in data.albums]

    with open("albums.json", "w") as file:
        json.dump(album_data, file, indent = 4)

# -- Testing -- #
if __name__ == "__main__":
    print()
    data: Manager = load_albums()
    print(data)