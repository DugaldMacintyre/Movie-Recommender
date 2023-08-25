import os
import requests
import urllib.parse
from sklearn.metrics.pairwise import cosine_similarity 
import numpy as np

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

CONFIG_PATTERN = 'http://api.themoviedb.org/3/configuration?api_key={key}'
IMG_PATTERN = 'http://api.themoviedb.org/3/movie/{imdbid}/images?api_key={key}' 
KEY = '99dd504960661c614f0547d8575cdb64'

def _get_json(url):
    r = requests.get(url)
    return r.json()

def get_poster_urls(imdbid):
    """ return image urls of posters for IMDB id
        returns all poster images from 'themoviedb.org'. Uses the
        maximum available size. 
        Args:
            imdbid (str): IMDB id of the movie
        Returns:
            list: list of urls to the images
    """
    config = _get_json(CONFIG_PATTERN.format(key=KEY))
    base_url = config['images']['base_url']
    sizes = config['images']['poster_sizes']

    """
        'sizes' should be sorted in ascending order, so
            max_size = sizes[-1]
        should get the largest size as well.        
    """
    def size_str_to_int(x):
        return float("inf") if x == 'original' else int(x[1:])
    max_size = max(sizes, key=size_str_to_int)

    posters = _get_json(IMG_PATTERN.format(key=KEY,imdbid=imdbid))['posters']
    poster_urls = []
    has_english_poster = False

    for poster in posters:
        iso_639_1 = poster["iso_639_1"]
        if iso_639_1 == "en":
            rel_path = poster['file_path']
            url = "{0}{1}{2}".format(base_url, max_size, rel_path)
            poster_urls.append(url)
            has_english_poster = True

    # If there's no English poster, use the first one (if available)
    if not has_english_poster and posters:
        for poster in posters:
            rel_path = posters[0]['file_path']
            url = "{0}{1}{2}".format(base_url, max_size, rel_path)
            poster_urls.append(url)

    return poster_urls

def weighted_rating(x, m, C):
    v = x['vote_count']
    R = x['vote_average']
    return (v/(v+m) * R) + (m/(m+v) * C)

def get_movie_indices(title, indices):
    error_flag = False
    try:
        idx = indices[title]
    except KeyError:
        raise MovieNotFoundError("Movie title not found. Please enter another film")

    if isinstance(idx, pd.Series):
        error_flag = True
        return idx, error_flag

    return idx, error_flag

def get_similar_movies(idx, md_numeric, cosine_sim):
    cosine_sim_numeric = cosine_similarity(np.array(md_numeric.iloc[idx]).reshape((1, -1)), md_numeric).reshape(-1)
    combined_scores = cosine_sim[idx] + cosine_sim_numeric

    sim_scores = list(enumerate(combined_scores))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:26]
    movie_indices = [i[0] for i in sim_scores]
    return movie_indices

def filter_qualified_movies(movie_indices, md, m):
    movies = md.iloc[movie_indices][['title', 'vote_count', 'vote_average', 'year', 'imdb_id', 'display_title']]
    vote_counts = movies[movies['vote_count'].notnull()]['vote_count'].astype('int')
    m = vote_counts.quantile(0.60)
    qualified = movies[(movies['vote_count'] >= m) & (movies['vote_count'].notnull()) & (movies['vote_average'].notnull())]
    return qualified

def improved_recommendations(C, title, md, md_numeric, cosine_sim, indices, m):
    idx, error_flag = get_movie_indices(title, indices)

    if error_flag:
        return md[md['title'] == title], error_flag
    
    movie_indices = get_similar_movies(idx, md_numeric, cosine_sim)
    qualified = filter_qualified_movies(movie_indices, md, m)
    qualified['vote_count'] = qualified['vote_count'].astype('int')
    qualified['vote_average'] = qualified['vote_average'].astype('int')
    qualified['wr'] = qualified.apply(weighted_rating, args=(m, C), axis=1)
    qualified = qualified.sort_values('wr', ascending=False).head(5)
    qualified['poster_url'] = qualified['imdb_id'].apply(lambda row: get_poster_urls(row)[0])
    return qualified, error_flag