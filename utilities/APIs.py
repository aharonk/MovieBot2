import json
import os

import requests

IMDBAPI_DAILY_CAP = 100  # free tier
OMDB_DAILY_CAP = 975  # the cap is really 1000, but why not let a bit of room?

########################################
# This bot uses two APIs.              #
#                                      #
# The first, IMDB-API, returns shallow #
# details about several movies close   #
# to what you searched for.            #
#                                      #
# The other, OMDBAPI, returns lots of  #
# details about the movie it decides   #
# is closest to what you searched for. #
########################################


def search_movie(movie_name):
    """Search for several movies closely matching the name we're searching for."""

    return requests.get('https://imdb-api.com/en/API/SearchMovie/' + os.getenv('IMDB_API_KEY') + '/' +
                        movie_name.replace(' ', '%20'))


def search_for_movies_with_name(movie_name):
    """Wrapper for search_movie that returns in JSON."""

    r = search_movie(movie_name)

    if r.status_code != 200:
        return None

    # Inconsistency in returning raw request vs JSON of text is probably a bad thing.
    return json.loads(r.text)


def request_movie(movie, is_id):
    """Get the movie with the matching IMDB ID (most accurate), or whatever movie OMDBAPI thinks has the closest name.
    It seems to be quite easy to get an empty response if the search title isn't close enough to the name of a movie."""
    return requests.get('https://www.omdbapi.com/?apikey=' + os.getenv('OMDB_KEY') +
                        '&i=' + movie if is_id else '&t=' + movie.replace(' ', '+'))
