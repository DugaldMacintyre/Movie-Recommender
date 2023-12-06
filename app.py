import os
import string
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import numpy as np

from helpers import apology, login_required, get_recommendations, MovieNotFoundError, get_movie_indices

from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


db = SQL("sqlite:///users.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show homepage"""


    return render_template("index.html")

@app.route("/history")
@login_required
def history():
    user_history = db.execute("select XXXXXXXXXX", session["user_id"])
    return render_template("history.html", movies=user_history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check for blank fields
        if not username:
            return apology("Username is a required field.")
        if not password:
            return apology("Password is a required field.")
        digits = 0
        special = 0
        for i in password:
            if i.isdigit():
                digits += 1
            if not i.isalnum():
                special += 1
        if len(password) < 5 or digits < 1 or special < 1:
            return apology("Password must be minimum 5 character long and have atleast 1 digit and 1 special character.")

        if not confirmation:
            return apology("Please confirm your password.")

        # check for password confirmation and hash
        if (password != confirmation):
            return apology("The given passwords do not match.")

        # check if username already exists
        if len(db.execute("SELECT username FROM users WHERE username = ?", username)) > 0:
            return apology("This username already exists!")

        # hash password and add to database
        hash_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, hash_password)

        # get user id
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # remember user id for session
        session["user_id"] = rows[0]["id"]
        return redirect("/")

    else:
        return render_template("register.html")
    

def initialize_global_variables():
    global C, title, md, md_numeric, cosine_sim, cosine_sim_numeric, indices, m
    
    # Load the cleaned movie data from CSV file
    md = pd.read_csv('data/cleaned_data.csv')

    md_numeric = md[['budget', 'popularity', 'revenue', 'runtime', 'Action', 'Adventure', 'Animation',
       'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy',
       'Foreign', 'History', 'Horror', 'Music', 'Mystery', 'Romance',
       'Science Fiction', 'TV Movie', 'Thriller', 'War', 'Western', 'series_count']]
    
    # Calculate C and m for weighted rating
    vote_counts = md[md['vote_count'].notnull()]['vote_count'].astype('int')
    vote_averages = md[md['vote_average'].notnull()]['vote_average'].astype('int')
    C = vote_averages.mean()
    m = vote_counts.quantile(0.95)
    
    # Calculate the cosine similarity matrix
    #tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0, stop_words='english')
    tf = TfidfVectorizer(dtype=np.float32, analyzer='word', ngram_range=(1, 2), min_df=2, max_df=0.80, stop_words='english')

    tfidf_matrix = tf.fit_transform(md['soup'])
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    # Create a Series of movie indices
    indices = pd.Series(md.index, index=md['title'])
    return

initialize_global_variables()

# TODO: ABLE TO DEAL WITH MULTIPLE MISSING FILMS
@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():

    movie_input = request.form.get('movie')
    titles = [title.strip().lower().translate(str.maketrans('', '', string.punctuation)).replace(" ", "") for title in movie_input.split(',')]

    indices = pd.Series(md.index, index=md['title'])
    try:
        recommended_movies_df, error_flag = get_recommendations(C, titles, md, cosine_sim, indices, m)
    except MovieNotFoundError as e:
        return render_template('index.html', error_message=str(e))
    
    recommended_movies_list = recommended_movies_df.to_dict('records')
    return render_template('index.html', recommended_movies=recommended_movies_list, error=error_flag)

@app.route("/recommendationsid", methods=["GET", "POST"])
def recommendations_id():
    titles = request.form.get('movie')

    indices = pd.Series(md.index, index=md['imdb_id'])

    try:
        recommended_movies_df, error_flag = get_recommendations(C, [titles], md, cosine_sim, indices, m)
    except MovieNotFoundError as e:
        return render_template('index.html', error_message=str(e))
    
    recommended_movies_list = recommended_movies_df.to_dict('records')
    return render_template('index.html', recommended_movies=recommended_movies_list, error=error_flag)

@app.route("/recommender")
@login_required
def recommender():
    return render_template("index.html")

# TODO: CHECK IF THIS IS WORKING
@app.route("/library")
@login_required
def library():
    reviews_list = db.execute("SELECT * FROM ratings WHERE user_id = ?", session["user_id"])
    movie_ids = list(set(entry['movie_id'] for entry in reviews_list))

    ratings = list(entry['rating'] for entry in reviews_list)
    reviews_list = md[np.isin(md['imdb_id'], movie_ids)].to_dict('records')

    movie_ratings = {entry['display_title']: rating for entry, rating in zip(reviews_list, ratings)}
    return render_template("library.html", movie_ratings=movie_ratings)

@app.route("/review", methods=["GET", "POST"])
def review():
    index_checker = pd.Series(md.index, index=md['title'])

    movie_input = request.form.get('movieToReview')
    rating_input = request.form.get('review')
    movie_input = [movie_input.strip().lower().translate(str.maketrans('', '', string.punctuation)).replace(" ", "")]
    index_checker = pd.Series(md.index, index=md['title'])

    idxs, error_flag, _ = get_movie_indices(movie_input, index_checker)
    
    if error_flag:
        recommended_movies_list = md[md['title'].isin(movie_input)].to_dict('records')
        return render_template('library.html', recommended_movies=recommended_movies_list, error=error_flag)

    for idx in idxs:
        imdb_id = md.iloc[idx]['imdb_id']

        # Check if a review for this user and movie already exists
        existing_review = db.execute("SELECT * FROM ratings WHERE user_id = ? AND movie_id = ?", session["user_id"], imdb_id)
        
        if len(existing_review) > 0:
            # If review exists, update it
            db.execute("UPDATE ratings SET rating = ? WHERE user_id = ? AND movie_id = ?", rating_input, session["user_id"], imdb_id)

        else:
            # If review doesn't exist, insert it
            db.execute("INSERT INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)", session["user_id"], imdb_id, rating_input)
    return render_template("library.html")

@app.route("/reviewid", methods=["GET", "POST"])
def review_id():
    index_checker = pd.Series(md.index, index=md['imdb_id'])

    movie_input = request.form.get('movieToReview')
    rating_input = request.form.get('review')

    movie_input = list(movie_input.strip().lower().translate(str.maketrans('', '', string.punctuation)).replace(" ", ""))
    index_checker = pd.Series(md.index, index=md['imdb_id'])

    idxs, error_flag, index = get_movie_indices(movie_input, index_checker)

    if error_flag:
        recommended_movies_list = md[md['title'].isin(movie_input)].to_dict('records')
        return render_template('library.html', recommended_movies=recommended_movies_list, error=error_flag)

    for idx in idxs:
        imdb_id = md.iloc[idx]['imdb_id']

        # Check if a review for this user and movie already exists
        existing_review = db.execute("SELECT * FROM ratings WHERE user_id = ? AND movie_id = ?", session["user_id"], imdb_id)
        
        if len(existing_review) > 0:
            # If review exists, update it
            db.execute("UPDATE ratings SET rating = ? WHERE user_id = ? AND movie_id = ?", rating_input, session["user_id"], imdb_id)

        else:
            # If review doesn't exist, insert it
            db.execute("INSERT INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)", session["user_id"], imdb_id, rating_input)
    return render_template("library.html")
    