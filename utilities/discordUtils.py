import discord


# region Get Messages From IDs
async def get_message_from_payload(payload: discord.RawReactionActionEvent, bot: discord.Bot):
    """Gets the message a reaction reacted to."""

    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    return message

# endregion


# region Embeds

def build_embed_from_IMDBAPI_movie_list(movie_list, five=False):
    """Builds an embed of length 3 or 5 with movies, their years of release, and their IMDB IDs (from IMDB-API).
    It's the easiest way to pass the ID around over an unknown length of time."""

    e = discord.Embed()
    e.title = movie_list['searchType'] + ": " + movie_list['expression']

    for i in range(0, min((5 if five else 3), len(movie_list['results']))):
        e.add_field(name=str(i + 1) + '.', value=movie_list['results'][i]['title'])
        e.add_field(name='Year', value=movie_list['results'][i]['description'][:4])
        e.add_field(name='IMDB ID', value=movie_list['results'][i]['id'])
    return e


def build_embed_from_OMDB_movie_details(movie):
    """Builds an embed with the details of the given movie. Movie details should be passed in as JSON from OMDBAPI."""

    e = discord.Embed()
    e.title = movie['Title']
    e.add_field(name='Year', value=movie['Year'])
    e.add_field(name='Rated', value=movie['Rated'])
    if len(movie['Ratings']) > 1 and movie['Ratings'][1]['Source'] == 'Rotten Tomatoes':
        e.add_field(name='Rotten Tomatoes', value=movie['Ratings'][1]['Value'])
    e.add_field(name='Genre', value=movie['Genre'])
    e.add_field(name='Director(s)', value=movie['Director'])
    e.add_field(name='Actors', value=movie['Actors'])
    e.add_field(name='Synopsis', value=movie['Plot'], inline=False)

    return e

# endregion


# region Reactions

async def add_reactions(message):
    """Populates a message with the :thumbsup: and :thumbsdown: emojis."""

    if isinstance(message, discord.Interaction):
        message = await message.original_response()
    await message.add_reaction('👍')
    await message.add_reaction('👎')


async def add_numeric_reactions(message, five=False):
    """Populates a message with the emojis :one: through :three: or :five:."""

    if isinstance(message, discord.Interaction):
        message = await message.original_response()
    await message.add_reaction('1️⃣')
    await message.add_reaction('2️⃣')
    await message.add_reaction('3️⃣')
    if five:
        await message.add_reaction('4️⃣')
        await message.add_reaction('5️⃣')


def get_emoji_val(emoji):
    """Used to get which movie in an embed to return when each emoji is pressed."""

    match emoji:
        case '1️⃣':
            return 0
        case '2️⃣':
            return 1
        case '3️⃣':
            return 2
        case '4️⃣':
            return 3
        case '5️⃣':
            return 4
        case _:
            return -1

# endregion


# region Send Messages

# The following three methods respond to a slash command or just send a message to the same channel.

async def respond(messageable, msg, ephemeral=False):
    await (messageable.respond(msg, ephemeral=ephemeral) if isinstance(messageable, discord.ApplicationContext)
           else messageable.send(msg))


async def respond_with_reactions(messageable, msg):
    message = await (messageable.respond(msg) if isinstance(messageable, discord.ApplicationContext)
                     else messageable.send(msg))
    await add_reactions(message)


async def respond_with_embed(messageable, embed):
    await (messageable.respond(embed=embed) if isinstance(messageable, discord.ApplicationContext)
           else messageable.send(embed=embed))


# The following four methods respond to a slash command.
async def followup(ctx, msg, ephemeral=False):
    await ctx.followup.send(msg, ephemeral=ephemeral)


async def followup_with_reactions(ctx, msg):
    message = await ctx.followup.send(msg)
    await add_reactions(message)


async def followup_with_embed(ctx, embed):
    await ctx.followup.send(embed=embed)


async def followup_with_movie_list_embed(ctx, content, movie_list, five=False):
    if movie_list is not None:
        resp = await ctx.followup.send(content=content, embed=build_embed_from_IMDBAPI_movie_list(movie_list, five))
        await add_numeric_reactions(resp, five)
        return

    await ctx.followup.send("Something went wrong, please try again.", ephemeral=True)

# endregion
