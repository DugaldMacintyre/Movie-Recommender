import os
import string
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, improved_recommendations, MovieNotFoundError

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
    global C, title, md, cosine_sim, indices, m
    
    # Load the cleaned movie data from CSV file
    md = pd.read_csv('data/cleaned_data.csv')
    
    # Calculate C and m for weighted rating
    vote_counts = md[md['vote_count'].notnull()]['vote_count'].astype('int')
    vote_averages = md[md['vote_average'].notnull()]['vote_average'].astype('int')
    C = vote_averages.mean()
    m = vote_counts.quantile(0.95)
    
    # Calculate the cosine similarity matrix
    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0, stop_words='english')
    tfidf_matrix = tf.fit_transform(md['soup'])
    cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
    
    # Create a Series of movie indices
    indices = pd.Series(md.index, index=md['title'])
    return

initialize_global_variables()

@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    title = request.form.get('movie')

    title = title.translate(str.maketrans('', '', string.punctuation))
    title = title.replace(" ", "")
    title = title.lower()

    try:
        recommended_movies_df, error_flag = improved_recommendations(C, title, md, cosine_sim, indices, m)
    except MovieNotFoundError as e:
        return render_template('index.html', error_message=str(e))
    
    recommended_movies_list = recommended_movies_df.to_dict('records')
    return render_template('index.html', recommended_movies=recommended_movies_list, error=error_flag)

@app.route("/recommendationsid", methods=["GET", "POST"])
def recommendations_id():
    title = request.form.get('movie')

    indices = pd.Series(md.index, index=md['imdb_id'])

    try:
        recommended_movies_df, error_flag = improved_recommendations(C, title, md, cosine_sim, indices, m)
    except MovieNotFoundError as e:
        return render_template('index.html', error_message=str(e))
    
    recommended_movies_list = recommended_movies_df.to_dict('records')
    return render_template('index.html', recommended_movies=recommended_movies_list, error=error_flag)