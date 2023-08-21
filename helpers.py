import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps

from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel

class MovieNotFoundError(Exception):
    pass

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def weighted_rating(x, m, C):
    v = x['vote_count']
    R = x['vote_average']
    return (v/(v+m) * R) + (m/(m+v) * C)

def get_movie_indices(title, indices):
    try:
        idx = indices[title]
    except KeyError:
        raise MovieNotFoundError("Movie title not found. Please enter another film")
    
    if isinstance(idx, pd.Series):
        idx = idx.iloc[0]  # Make selection user defined when frontend implemented
    return idx

def get_similar_movies(idx, cosine_sim):
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:26]
    movie_indices = [i[0] for i in sim_scores]
    return movie_indices

def filter_qualified_movies(movie_indices, md, m):
    movies = md.iloc[movie_indices][['title', 'vote_count', 'vote_average', 'year']]
    vote_counts = movies[movies['vote_count'].notnull()]['vote_count'].astype('int')
    m = vote_counts.quantile(0.60)
    qualified = movies[(movies['vote_count'] >= m) & (movies['vote_count'].notnull()) & (movies['vote_average'].notnull())]
    return qualified

def improved_recommendations(C, title, md, cosine_sim, indices, m):
    idx = get_movie_indices(title, indices)
    movie_indices = get_similar_movies(idx, cosine_sim)
    qualified = filter_qualified_movies(movie_indices, md, m)
    qualified['vote_count'] = qualified['vote_count'].astype('int')
    qualified['vote_average'] = qualified['vote_average'].astype('int')
    qualified['wr'] = qualified.apply(weighted_rating, args=(m, C), axis=1)
    qualified = qualified.sort_values('wr', ascending=False).head(5)
    return qualified