import json
from datetime import datetime
from enum import Enum

from utilities import database, APIs

db = database.DBConnection()


class ResponseType(Enum):
    EPHEMERAL = 1
    NUMERIC = 2
    YES_NO = 3
    EMBED = 4


def check_api_allowance(limit, add=1):
    """Check whether today's API calls exceeds the number allowed for the given API.
    Since both will be called each time one is, the method does not always increment the count."""

    res = db.get_calls_on_date(datetime.now().date())
    if not res:
        db.add_date_with_base_calls(datetime.now().date(), add)
    elif add != 0 and res[0][0] < limit:
        db.increment_calls_on_date(datetime.now().date())

    return (not res) or res[0][0] < limit


def check_IMDBAPI_allowance(add=1):
    return check_api_allowance(APIs.IMDBAPI_DAILY_CAP, add)


def check_OMDB_allowance(add=1):
    return check_api_allowance(APIs.OMDB_DAILY_CAP, add)


def vote(movie_name, vote):
    """Wrapper for database.vote so the bot doesn't need to import it."""
    db.vote(movie_name, vote)


def get_list_of_similar_movies(movie_name):
    """Returns a list of movies with names close to the search term, or an error message if the API call fails."""
    movies_list = APIs.search_for_movies_with_name(movie_name)
    return ((movies_list, ResponseType.NUMERIC) if (movies_list is not None)
            else ("Something went wrong, please try again.", ResponseType.EPHEMERAL))


def add_movie(movie_name: str, search: bool):
    """If we can search, return a list of options.
    Otherwise, just add the given title (cleaned up a bit) to the database. """

    # Check on API usage
    if not check_OMDB_allowance():
        return 'No more movies can be added today. Please try again tomorrow.', ResponseType.EPHEMERAL

    # Check if we can use the search API
    if search and check_IMDBAPI_allowance(0):
        return get_list_of_similar_movies(movie_name)
    else:
        return finish_movie_add(movie_name, False)


def movie_details(movie_name: str, search: bool, year):
    """If we can search, return a list of options.
    Otherwise, return the details of the movie we can find with the closest name."""

    if not check_OMDB_allowance():
        return 'No more movies can be dealt with today. Please try again tomorrow.', ResponseType.EPHEMERAL

    if search and check_IMDBAPI_allowance(0):
        # Year helps narrow down the options. "The lord of the rings" doesn't get Ralph Bakshi's... masterpiece.
        return get_list_of_similar_movies(movie_name + ('' if year is None else (' ' + year)))
    else:
        return finish_movie_details(movie_name, False)


def list_movies():
    return db.get_top_10_movies_pretty()


def finish_movie_add(movie, is_id):
    """Attempts to add the given movie to the database."""

    # Even if we can't use the search API, get the official name of *a* movie
    r = APIs.request_movie(movie, is_id)
    http_resp = json.loads(r.text)

    if r.status_code != 200 or http_resp['Response'] == 'False':
        return f"Sorry, I couldn't find {movie}.", ResponseType.EPHEMERAL
    else:
        movie_name = http_resp['Title']
        if db.add_movie(movie_name):
            return f'{movie_name}', ResponseType.YES_NO
        else:
            return f'{movie_name} is on the list already.', ResponseType.EPHEMERAL


def finish_movie_details(movie, is_id):
    """Returns details about a movie, accuracy varies based on use of ID or title."""

    # Even if we can't use the search API, get the official name of *a* movie
    r = APIs.request_movie(movie, is_id)
    http_resp = json.loads(r.text)

    if r.status_code != 200 or http_resp['Response'] == 'False':
        return f"Sorry, I couldn't find details about {movie}.", ResponseType.EPHEMERAL
    else:
        return http_resp, ResponseType.EMBED
