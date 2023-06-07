import os

import discord
from discord import option
from dotenv import load_dotenv

import movies
from movies import ResponseType
from utilities import discordUtils

load_dotenv()
bot = discord.Bot()

####################################################
# We'll get this over with here.                   #
# There are probably a lot of things I could have  #
# done much more efficiently due to my lack of     #
# experience with the libraries.                   #
#                                                  #
# You've been warned.                              #
####################################################
movie_add_confirmation = 'Which movie did you have in mind?'
movie_details_confirmation = 'Which movie would you like details on?'


# region Events

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.event
async def on_raw_reaction_add(payload):
    """If a list of movies has been reacted to with a number,
    add/display details of that movie, whichever is appropriate.
    If a movie has been reacted to with a thumbs up or down, adjust the vote db accordingly."""

    if payload.user_id == bot.user.id:
        return

    message = await discordUtils.get_message_from_payload(payload, bot)

    # Wouldn't want to do random things with peoples' messages.
    if message.author.id != bot.user.id:
        return

    reaction = str(payload.emoji)

    # I wanted to do a cool character/int subtraction using 1️⃣, but I couldn't figure out how to separate the Unicode.
    if '1️⃣' <= reaction <= '5️⃣':
        if message.content == movie_add_confirmation:
            await message.delete()
            # A list of movies is created (see utilities.discordUtils.build_embed_from_IMDBAPI_movie_list) with rows of
            # (movie_name, year, imdb_id). We want the id, resulting in second parameter.
            # See APIs.request_movie for why we want the ID.
            # There *should* be only one embed.
            await finish_movie_add(payload.channel_id,
                                   message.embeds[0].fields[3 * discordUtils.get_emoji_val(reaction) + 2].value)
        elif message.content == movie_details_confirmation:
            await message.delete()
            await finish_movie_details(payload.channel_id,
                                       message.embeds[0].fields[3 * discordUtils.get_emoji_val(reaction) + 2].value)
    else:
        if reaction == '👍':
            movies.vote(message.content, 1)
        elif reaction == '👎':
            movies.vote(message.content, -1)


@bot.event
async def on_raw_reaction_remove(payload):
    """If a vote is taken back, remove said vote."""
    reaction = str(payload.emoji)

    # There's probably some way to consolidate this with the 'else' in on_raw_reaction_add.
    if reaction == '👍':
        msg = await discordUtils.get_message_from_payload(payload, bot)
        movies.vote(msg.content, -1)
    elif reaction == '👎':
        msg = await discordUtils.get_message_from_payload(payload, bot)
        movies.vote(msg.content, 1)


# endregion


# region Slash Commands

# I'm not sure how to capitalize/add spaces to the name. I got errors when I tried.
@bot.slash_command(name="add_movie", description="Add a movie to the watch list.")
@option("search", description="Choose this if you would like to choose from several results", required=False,
        default=True)
async def add_movie(ctx, movie_name: str, search: bool):
    """Add a movie to the watchlist."""

    await ctx.defer()  # required if it will take over 3 seconds to respond.

    await send_ctx_response(ctx, movies.add_movie(movie_name, search), True)


@bot.slash_command(name='movie_details', description="View the details of a movie.")
@option("search", description="Choose this if you would like to choose from several results", required=False,
        default=True)
@option("year", description="Specify a year of release", required=False, default=None)
async def movie_details(ctx, movie_name: str, year: str | None, search: bool):
    """Get the details of a movie.
    Details are decided on by the build_embed_from_OMDB_movie_details in discordUtils.py"""

    await ctx.defer()

    await send_ctx_response(ctx, movies.movie_details(movie_name, search, year), False)


@bot.slash_command(name='list_movies', description="List the top ten movies on the list in order of popularity.")
async def list_movies(ctx):
    await discordUtils.respond(ctx, movies.list_movies(), False)


# endregion


# region Helper Methods

# The following two methods are used by on_raw_reaction_add. To allow for the reader to take time (and/or forget),
# and for cleaner responses, the original response to the slash command is deleted,
# leaving only the movie title or details in the channel.

async def finish_movie_add(channel_id, movie):
    """Sends the movie and vote options (or error message) to the channel."""
    await send_channel_response(channel_id, movies.finish_movie_add(movie, True))


async def finish_movie_details(channel_id, movie):
    """Sends the movie details (or error message) to the channel."""
    await send_channel_response(channel_id, movies.finish_movie_details(movie, True))


async def send_channel_response(channel_id: int, response_with_type: tuple):
    """Sends a message to the channel based on the type of response."""

    channel = bot.get_channel(channel_id)

    match response_with_type[1]:
        case ResponseType.EPHEMERAL:
            await discordUtils.respond(channel, response_with_type[0])
        case ResponseType.YES_NO:
            await discordUtils.respond_with_reactions(messageable=channel, msg=response_with_type[0])
        case ResponseType.EMBED:
            await discordUtils.respond_with_embed(channel, discordUtils.build_embed_from_OMDB_movie_details(
                response_with_type[0]))


async def send_ctx_response(ctx, response_with_type: tuple, for_add: bool):
    """Responds to a slash command based on the type of response."""

    match response_with_type[1]:
        case ResponseType.EPHEMERAL:
            await discordUtils.followup(ctx, response_with_type[0], True)
        case ResponseType.NUMERIC:
            await discordUtils.followup_with_movie_list_embed(ctx=ctx,
                                                              content=(movie_add_confirmation if for_add
                                                                 else movie_details_confirmation),
                                                              movie_list=response_with_type[0])
        case ResponseType.YES_NO:
            await discordUtils.followup_with_reactions(ctx, response_with_type[0])
        case ResponseType.EMBED:
            await discordUtils.followup_with_embed(ctx, discordUtils.build_embed_from_OMDB_movie_details(
                response_with_type[0]))

# endregion


bot.run(os.getenv('TOKEN'))
