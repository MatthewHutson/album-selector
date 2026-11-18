# -- Imports -- #
from __future__ import annotations
from classes import *
from selector_functions import *
from loading import *
from datetime import timedelta
from dotenv import load_dotenv # type: ignore
from asyncio import sleep
from copy import deepcopy
import discord # type: ignore
import os
import subprocess

# -- Bot Setup -- #
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN = os.getenv('ADMIN')
PREFIX = os.getenv("PREFIX")

intents = discord.Intents(2048)
intents.polls = True
intents.messages = True
client = discord.Client(intents = intents)
active_operations: int = 0

# -- Functions -- #
def create_poll(name: str, answers: list[str], multiple: bool = False, time: timedelta = timedelta(hours = 1)) -> discord.Poll:
    new_poll = discord.Poll(question = name, duration = time, multiple = multiple)

    for i in range(len(answers)):
        new_poll._answers[i] = discord.PollAnswer.from_params(id = i, text = answers[i], poll = new_poll, message = None)

    return new_poll

def get_winner(poll: discord.Poll) -> str:
    '''Since the in built bethod isn't working lol'''
    answers: list[discord.PollAnswer] = poll.answers
    highest_vote_count: int = 0 
    best_response: discord.PollAnswer = None

    for answer in answers:
        if answer.vote_count > highest_vote_count:
            best_response = answer
            highest_vote_count = answer.vote_count

    if best_response is None:
        return None
    else:
        return best_response.text
    
def add_admin_commands(user: discord.User) -> dict:
    # -- Get Admin Commands -- #
    global admin, commands, admin_commands

    total_commands = {PREFIX + command: function for command, function in commands.items()}

    if user.id == admin.id: 
        for command, function in admin_commands.items():
            total_commands[PREFIX + command] = function

    return total_commands

async def user_select(user: discord.User, name: str, answers: list[str], time: float = 300, multiple: bool = False) -> str:
    '''DMs a user with a poll to make a selection'''
    global active_operations

    hours: int =  (time // 3600)
    minutes: int = ((time // 60) % 60)
    seconds: int =  (time % 60)

    if hours != 0: fake_duration = timedelta(hours = hours, minutes = minutes, seconds= seconds)
    else: fake_duration = timedelta(hours = 1)

    time_text: str = f" ({"0" + str(hours) if hours < 10 else hours}:{"0" + str(minutes) if minutes < 10 else minutes}:{"0" + str(seconds) if seconds < 10 else seconds})"

    poll = create_poll(name + time_text, answers, multiple, fake_duration)
    await user.send(poll = poll)

    try: await client.wait_for("poll_vote_add", timeout = time)
    except: pass

    await poll.end()
    await sleep(3)
    
    answer = get_winner(poll)

    return answer

async def select_album(user: discord.User, args: list[str] = [], time: float = 300) -> None:
    '''Send a short, medium and long album in a poll'''

    data: Manager = load_albums(user.id)
    selections: Manager = output_selection(data)

    if len(selections.albums) != 0:
        album_dict: dict = create_poll_data(selections)
        answers = list(album_dict.keys()) + ["Reroll"]

        answer = await user_select(user, "Select an Album", answers, time)

        if answer == "Reroll":
            await select_album(user, args, time)
        else:
            album: Album = album_dict[answer]
            album.listen_count += 1
            save_data(user.id, data)
    else:
        await user.send(content = f"No albums saved for {user.display_name}")
        
async def bot_help(user: discord.User, args: list[str] = []) -> None:
    '''Recieve a list of bot commands'''

    total_commands = add_admin_commands(user)

    await user.send(content = "Command List:")

    for name, function in total_commands.items():
        await user.send(content = f"> {name} - {function.__doc__}")

async def stop(user: discord.User, args: list[str] = []) -> None:
    '''Terminate the bot'''

    if active_operations == 1: await client.close()
    else: await user.send(content = "Bot too busy to shut down.")

    print(f"\n{client.user} is now offline.\n")

async def add_album(user: discord.User, args: list[str] = []):
    '''Add a new album to your saved albums'''

    if len(args) == 4:
        try:
            args[2] = int(args[2]) # -- Duration
            args[3] = int(args[3]) # -- Year

            assert args[2] >= 0
            assert args[3] >= 0 
        except:
            await user.send(content = f"**Invalid Arguments**: duration and/or year is not a valid positive integers!")
        else:
            album = Album(*args)
            data: Manager = load_albums(user.id)
            possible_albums = data.get_albums(album.name, album.artist)

            if len(str(album)) < 50 and len(possible_albums) == 0:

                await user.send(content = f"Are you sure you want to add **{album.name}** by **{album.artist}** that has a duration of **{album.time}** (h:m) and was released in **{album.year}**?")
                result = await user_select(user, f"Add {album.name} to your file?", ["Yes", "No"], time = 30)

                if result == "Yes":
                    data.add(album)
                    save_data(user.id, data)
                    await user.send(content = f"{album} successfully added!")

            elif len(possible_albums) != 0:
                await user.send(content = f"**ERROR**: An album named **{album.name}** by **{album.artist}** already exists in your save!")

            elif len(str(album)) >= 50:
                await user.send(content = "**ERROR**: Too many characters in the name and artist name combined for discord to handle!")

    else:
        await user.send(content = "**Invalid Arguments**: requires **[name], [artist], [duration (minutes)], [release year]**")

async def update(user: discord.User, args: list[str] = []) -> None:
    '''Updates and restarts the bot'''

    if active_operations == 1:
        await client.close()
        print(f"\n{client.user} is now offline.\n")
        subprocess.run(["bash", "bot.sh"], shell = True)
    else:
        await user.send(content = "Bot too busy to restart.")

async def remove(user: discord.User, args: list[str] = []) -> None:
    '''Remove an album from your saved albums.'''
    if len(args) == 2:
        name: str = args[0]
        artist: str = args[1]
        data: Manager = load_albums(user.id)
        possible_albums = data.get_albums(name, artist)

        if len(possible_albums) != 0:
            out: str = await user_select(user, f"Are you sure you want to remove {name} by {artist}?", ["Yes", "No"], time = 30)

            if out == "Yes":
                album: Album = possible_albums[0]
                data.remove(album)
                save_data(user.id, data)
        

        else: await user.send(content = f"**ERROR**: No album named **{name}** was found!")

    else:
        await user.send(content = f"**Invalid Arguments**: Please Provide **[Name], [Artist]** as arguments!")

async def active_count(user: discord.User, args: list[str] = []) -> None:
    '''Get the current number of active operations performed by the bot'''
    await user.send(content = f'There {"are" if active_operations != 1 else "is"} {active_operations} active operation{"s" if active_operations != 1 else ""} right now!')
    
# -- Events -- #
@client.event
async def on_ready() -> None:
    global admin

    admin = await client.fetch_user(ADMIN)
    print(f'{client.user} has connected to Discord!\n')

@client.event
async def on_message(msg: discord.Message) -> None:
    global active_operations, commands, admin_commands

    user: discord.User = msg.author 

    if user != client.user:
        total_commands = add_admin_commands(user)

        setup: list[str] = msg.content.split(" ", maxsplit = 1)
        command = setup[0]
        
        args: list[str] = setup[1].split(", ") if len(setup) != 1 else []

        prev_active_polls = active_operations
        active_operations += 1

        try:
            if command in total_commands.keys():
                function: Callable = total_commands[command]
                await function(user = user, args = args)

        except Exception as e:
            if prev_active_polls != active_operations:
                active_operations -= 1

            raise e

        active_operations -= 1

# -- Other Setup -- #
commands: dict[str, Callable[[discord.User, list[str]], None]] = {
    "help": bot_help,
    "suggest": select_album,
    "add": add_album,
    "remove": remove
}

admin_commands : dict[str, Callable[[discord.User, list[str]], None]] = {
    "update": update,
    "stop": stop,
    "active_count": active_count
}

# -- Main Function -- #
def run_bot() -> None:
    try: client.run(TOKEN)
    except Exception as e: raise e

if __name__ == "__main__":
    run_bot()