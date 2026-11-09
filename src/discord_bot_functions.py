# -- Imports -- #
from __future__ import annotations
from classes import *
from selector_functions import *
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

async def user_select(user: discord.User, name: str, answers: list[str], time: float = 60, multiple: bool = False) -> str:
    '''DMs a user with a poll to make a selection'''

    fake_duration = timedelta(hours = 1)

    poll = create_poll(name, answers, multiple, fake_duration)
    await user.send(poll = poll)

    try: await client.wait_for("poll_vote_add", timeout = time)
    except: pass

    await poll.end()
    await sleep(2)
    
    answer = get_winner(poll)

    return answer
    
# -- Events -- #
@client.event
async def on_ready():
    # -- Bot Main -- #
    print(f'{client.user} has connected to Discord!')

    answers = ["Yes", "No"]
    user = await client.fetch_user(USER)
    answer = await user_select(user, "Test 3", answers)

    if answer != None:
        await user.send(f"The Result is {answer}")
    else:
        await user.send("The Result is None")

# -- Main Function -- #
def run_bot() -> None:
    try:
        client.run(TOKEN)
    except Exception as e:
        raise e.with_traceback()

if __name__ == "__main__":
    run_bot()