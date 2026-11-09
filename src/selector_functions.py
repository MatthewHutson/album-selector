# -- Imports -- #
from classes import *
from random import choice

# -- Functions -- #
def first(data: Manager, num: int) -> dict[str, list[Album]]:
    '''Filters the first [num] albums in each category orderd by number of listens'''
    categories = {
        "short": sorted(data.short, key = lambda a: a.listen_count),
        "medium": sorted(data.medium, key = lambda a: a.listen_count),
        "long": sorted(data.long, key = lambda a: a.listen_count)
    }

    for category, albums in categories.items():
        categories[category] = albums[:num]

    return categories

def selction(data: Manager, num: int = 3) -> tuple[Album, Album, Album]:
    '''Selects a random album from the filtered albums'''
    possibilities: dict = first(data, num)

    short_album: Album = choice(possibilities["short"])
    medium_album: Album = choice(possibilities["medium"])
    long_album: Album = choice(possibilities["long"])

    return short_album, medium_album, long_album

def output_selection(data: Manager) -> Manager:
    '''Outputs the selection from the manager'''
    short_album, medium_album, long_album = selction(data)
    out_manager = Manager([short_album, medium_album, long_album])

    return out_manager

# -- Testing -- #
if __name__ == "__main__":
    albums = []

    for i in range(20):
        temp = Album(str(i), "test", 10 * i, i)
        albums.append(temp)

    data = Manager(albums)

    print()
    print(first(data, 5))
    print()
    print(selction(data))
    print()
    print(str(output_selection(data)))