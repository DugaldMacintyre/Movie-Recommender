# Movie-Recommender

### Table of Contents

1. [Project Motivation](#motivation)
2. [File Descriptions](#files)
3. [Technologies Used](#technologies)
4. [To-Dos](#todo)

## Project Motivation<a name="motivation"></a>
We both love movies, discovering new ones, and talking about them! Hence, we decided we wanted to explore recommendation systems and create our own application that suggests films to us. Through this, we wanted to gain experience creating full-stack applications, databases, and data science concepts. Further, we both like to work in a team and discuss ideas and this felt like the perfect opportunity. We hope you enjoy!

## File Descriptions <a name="files"></a>
### app.py
Main file where routes and requests are taken care. Film recommendations are calculated and returned here. Reviews are also dealt with.

### helpers.py
Helper functions to recommend movies and add reviews are. 

### testing.ipynb
A data cleaning pipeline and write the new dataframe to a cv for use in the application. Testing of content-based and collaborative recommender systems. 

## Technologies Used <a name="technologies"></a>
<a target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="python" width="40" height="40" /> </a>
&nbsp; &nbsp;
<a target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/pandas/pandas-original.svg" alt="pandas" width="40" height="40" /> </a>
&nbsp; &nbsp;
<a target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/flask/flask-original.svg" alt="pandas" width="40" height="40" /> </a>
&nbsp; &nbsp;
<a target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/jupyter/jupyter-original.svg" alt="pandas" width="40" height="40" /> </a>
&nbsp; &nbsp;

## [To-Dos <a name="todo"></a>
* Able to deal with multiple missing films (use The Dark Knight and Heat as a test case).
* Check if updating database with new review is working.
* Fid nav to DEAL smaller screens
* Improve on and add styling for smaller screens for reviews page
* Consider using MinMaxScaler when scaling scores
* Implement collaborative recommender in app.py
