from flask import Flask, render_template, request, jsonify, json, url_for, abort, redirect, session,flash
import requests
from cassandra.cluster import Cluster
from cassandra.cqlengine import connection
from flask_sqlalchemy import sqlalchemy, SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from userDB.setupDB import user
from flask_restful import Api

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPOGATE_EXCEPTIONS'] = True
#app.config['SECRET_KEY'] = '{Your Secret Key}'

api = Api(app)
db = SQLAlchemy(app)

api.add_resource(user, '/auth.db')
api.add_resource(movie_list, '/list.db')

class movie_list(db.model):
  
  listname = "movie_list"
  
  l_id = db.Column(db.Integer, 
                 primary_key=True)
  
  username_reviewer = db.Column(db.String(100), 
                                unique=True, 
                                nullable=False)
  
  movie_name = db.Column(db.String(100), 
                         nullable=False)
  
  director = db.Column(db.String(100), 
                       nullable=False)
  
  year = db.Column(db.int(4), 
                   nullable=False)
  
  score = db.Column(db.float(),
                    nullable=True)
  
  def __repr__(self):
        return '' % self.id

class user(db.Model):
  
  table_name = "user_list"
  
  uid = db.Column(db.Integer, 
                  primary_key=True)
  
  username = db.Column(db.String(100), 
                       unique=True, 
                       nullable=False)
  
  pass_hash = db.Column(db.String(100), 
                        nullable=False)

  def __repr__(self):
    return '' % self.username

    
@app.route("/signup/", methods=["GET", "POST"])
def signup():
    """
    Implements signup functionality. Allows username and password for new user.
    Hashes password with salt using werkzeug.security.
    Stores username and hashed password inside database.
    Username should to be unique else raises sqlalchemy.exc.IntegrityError.
    """

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if not (username and password):
            flash("Username or Password cannot be empty")
            return redirect(url_for('signup'))
        else:
            username = username.strip()
            password = password.strip()

        # Returns salted pwd hash in format : method$salt$hashedvalue
        hashed_pwd = generate_password_hash(password, 'sha256')

        new_user = user(username=username, pass_hash=hashed_pwd)
        db.session.add(new_user)

        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            flash("Username {u} is not available.".format(u=username))
            return redirect(url_for('signup'))

        flash("User account has been created.")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/", methods=["GET", "POST"])
@app.route("/login/", methods=["GET", "POST"])
def login():
    """
    Provides login functionality by rendering login form on get request.
    On post checks password hash from db for given input username and password.
    If hash matches redirects authorized user to home page else redirect to
    login page with error message.
    """

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if not (username and password):
            flash("Username or Password cannot be empty.")
            return redirect(url_for('login'))
        else:
            username = username.strip()
            password = password.strip()

        user = user.query.filter_by(username=username).first()

        if user and check_password_hash(user.pass_hash, password):
            session[username] = True
            return redirect(url_for("user_home", username=username))
            flash("Invalid username or password.")

    return render_template("login_form.html")

@app.route("/user/<username>/", methods = ["GET", "POST"])
def user_home(username):
    if request.method == "GET":
        url = "https://owen-wilson-wow-api.herokuapp.com/wows/random"
        resp = requests.get(url)
        response = resp.json()
        movie = response[0].get('movie')
        director = response[0].get('director')
        year = response[0].get('year')
        
    if request.method == "POST":
        
        rating = request.form["rating"]
        list_entry = movie_list(username_reviewer = username, 
                                movie_name = movie,
                                director = director,
                                year = year,
                                score = rating)
        
        db.session.add(list_entry)
        db.session.commit()
        
        return [movie, director, year]

    return render_template("user_home.html", username=username, movie=movie, director=director, year=year)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
