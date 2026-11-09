# -- Imports -- #
from __future__ import annotations
from classes import *
from selector_functions import *
from loading import *
from dotenv import load_dotenv
from datetime import timedelta
from asyncio import sleep
import discord
import os

# -- Bot Setup -- #
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
USER = os.getenv('USER')
GUILD = os.getenv('GUILD')

intents = discord.Intents(2048)
intents.polls = True
intents.messages = True
client = discord.Client(intents = intents)

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

async def user_select(user: discord.User, name: str, answers: list[str], time: float = 300, multiple: bool = False) -> str:
    '''DMs a user with a poll to make a selection'''

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

async def select_album(user: discord.user, time: float = 1800) -> Album | None:
    '''DMs the user to select one of the albums in the JSOn file before saving it'''
    data: Manager = load_albums()
    selections: Manager = output_selection(data)
    album_dict: dict = create_poll_data(selections)
    answers = list(album_dict.keys()) + ["Reroll"]

    answer = await user_select(user, "Select an Album", answers, time)

    if answer is None:
        return None
    elif answer == "Reroll":
        return await select_album(user, time)
    else:
        album: Album = album_dict[answer]
        album.listen_count += 1
        save_data(data)
        return album
    
# -- Events -- #
@client.event
async def on_ready() -> None:
    # -- Bot Main -- #
    print(f'{client.user} has connected to Discord!')

    user = await client.fetch_user(USER)
    await select_album(user)

@client.event
async def on_message(msg: discord.Message) -> None:
    if msg.author != client.user:
        user = await client.fetch_user(USER)

        if msg.content == "!prompt" and msg.author == user:
            await select_album(user)

# -- Main Function -- #
def run_bot() -> None:
    try: client.run(TOKEN)
    except Exception as e: pass

if __name__ == "__main__":
    run_bot()