import os
import sqlite3

from dotenv import load_dotenv

#######################################################
# The database has two tables.                        #
#                                                     #
# The first table, daily_api_calls, has two columns.  #
# A date (in string form; SQLite doesn't easily       #
# have dates) and the number of calls on that date.   #
#                                                     #
# The second table, movies, has a column for movie    #
# titles (sorry for the formatting inconsistency)     #
# and a column to keep track of votes for that movie. #
#######################################################


class DBConnection:
    def __init__(self):
        load_dotenv()
        self.conn = sqlite3.connect(os.getenv('DB_PATH'))
        self.cursor = self.conn.cursor()

    def get_calls_on_date(self, target_date):
        self.cursor.execute('SELECT calls FROM daily_api_calls WHERE date = ?', (target_date,))
        return self.cursor.fetchall()

    def add_date_with_base_calls(self, target_date, base_calls):
        self.cursor.execute('INSERT INTO daily_api_calls ("date", calls) VALUES (?, ?)', (target_date, base_calls))
        self.conn.commit()

    def increment_calls_on_date(self, target_date):
        # `calls = calls + 1` doesn't work for some reason, I need to pass in 1.
        self.cursor.execute('UPDATE daily_api_calls SET calls = calls + ? WHERE date = ?', (1, target_date))
        self.conn.commit()

    def add_movie(self, movie_name):
        """Try to add a movie to the movies table.
        Returns whether the operation succeeded (i.e. returns false if the movie is already present)."""

        try:
            self.cursor.execute('INSERT INTO movies (Movie_Name) VALUES (?)', (movie_name,))
            self.conn.commit()
            return True
        except sqlite3.Error as _:
            return False

    def get_top_10_movies_pretty(self):
        """Get the top 10 movies with the most votes, formatted in rows of '<#votes> - <movie_title>'."""

        self.cursor.execute('''SELECT Movie_Name, Votes FROM movies ORDER BY Votes DESC LIMIT 10''')
        movie_list = ''
        for movie in self.cursor.fetchall():
            movie_list += str(movie[1]) + ' - ' + movie[0] + "\n"
        return movie_list

    def vote(self, movie_name, vote):
        self.cursor.execute('UPDATE movies SET Votes = Votes + ? WHERE Movie_Name = ?', (vote, movie_name,))
        self.conn.commit()
