import os
import sys
from flask import Flask, redirect, render_template, request, flash, session, g, abort
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Track, UserTrack
from forms import UserAddForm, LoginForm, UserEditForm
from sqlalchemy.exc import IntegrityError
from urllib.parse import quote, quote_plus
import logging
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///capstone_spotify_db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
# Having the Debug Toolbar show redirects explicitly is often useful;
# however, if you want to turn it off, you can uncomment this line:
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "up_the_planes")
debug = DebugToolbarExtension(app)

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)

connect_db(app)

# Do I need to be doing this everytime the app file is run?
# or should it be a one-time thing? (kinda thinking the latter)
db.create_all()


##############################################################################
# User signup/login/logout
# DK - This is taken from the Warbler project; amendments may yet need be made

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None


def do_login(user):
    """Login user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data
            )
            db.session.commit()

        ###########
        # This is where I need to differentiate between which field requirements are being violated
        # (i.e. username, email, (more?))
        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle user logout."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


#############################################################
# User routes


@app.route('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)
    # ################### QUESTION ############################
    # I'm not sure how to do this with the Many2Many I have set up;
    # would it be (more) like the messages, or the likes below?
    # messages = (Message
    #             .query
    #             .filter(Message.user_id == user_id)
    #             .order_by(Message.timestamp.desc())
    #             .limit(100)
    #             .all())
    # likes = [message.id for message in user.likes]
    return render_template('users/show.html', user=user)


@app.route('/users/follow/<int:track_id>', methods=['POST'])
def add_follow(track_id):
    """Adds indicated track to user's personal on-site library."""

    if not g.user:
        flash("Access unauthorized!", "danger")
        return redirect('/')

    followed_track = Track.query.get_or_404(track_id)
    g.user.tracks.append(followed_track)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.route('/users/stop-following/<int:track_id>', methods=['POST'])
def stop_following(track_id):
    """Removes indicated track from user's personal on-site library."""

    if not g.user:
        flash("Access unauthorized!", "danger")
        return redirect('/')

    followed_track = Track.query.get(track_id)
    g.user.tracks.remove(followed_track)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


@app.route('/users/profile', methods=['GET', 'POST'])
def edit_profile():
    """Updates profile for current user."""

    if not g.user:
        flash('Access unauthorised!', 'danger')
        return redirect('/')

    user = g.user
    form = UserEditForm(obj=user)

    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            user.username = form.username.data
            user.email = form.email.data

            db.session.commit()
            return redirect(f'/users/{user.id}')

        flash("Incorrect password, please reenter.", "danger")

    return render_template('users/edit.html', form=form, user_id=user.id)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized!", "danger")
        return redirect('/')

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect('/signup')


# ########## TRACKS ROUTES ###############

@app.route('/tracks')
def list_tracks():
    """Page with listing of tracks (up to 100(?));
    can take a 'q' parameter in querystring to search by that track name. """

    search = request.args.get('q')

    if not search:
        tracks = (Track
                  .query
                #   ALSO can make this a variable ORDER_BY;
                #   certainly Artist, Album (when implemented);
                #   but DEFINITELY also the AudioFeatures categories
                #   (I say definitely b/c this is really where the NOVELTY of the site is located):
                #   Acousticness/Danceability/Duration/Energy/Instrumentalness/
                #   Key/Liveness/Mode/Speechiness/Tempo/Time Signature/Valence
                #   
                  .order_by(Track.name.asc())
                #   Can PAGINIATE this somehow;
                #   has to do w/a variable OFFSET;
                #   TO-DO after First Draft done
                  .limit(100)
                  .all())
    else:
        tracks = Track.query.filter(Track.name.like(f"%{search}%"))

    return render_template('tracks/index.html', tracks=tracks)


@app.route('/tracks/<int:track_id>', methods=['GET'])
def show_track(track_id):
    """Show unpacking of an individual track"""

    track = Track.query.get_or_404(track_id)
    return render_template('tracks/show.html', track=track)

# #####################
# THIS ONE NEEDS WORK:
@app.route('/tracks/search')
def search_track(track_spotify_id):
    """Searches local db for track based on its spotify id."""

    # How can I make sure that it's looking for a Track based on the SPOTIFY id, not just the basic id?
    db_track = Track.query.filter(Track.spotify_id == track_spotify_id).all()
    track_id = db_track.id

    return redirect("/tracks/<int:track_id>")


########## HOMEPAGE/ETC ROUTES ################


@app.route('/')
def root():
    """Show homepage"""


    if g.user:
        return render_template('home.html')
    
    else:
        return render_template('home-anon.html')


@app.route('/search', methods=['GET', 'POST'])
def search_spotify():
    """Handles a search of the Spotify database
        and returns a list of items (currently just tracks)
        to populate the search-results <div>."""

    search = request.args.get('q')
    tracks = []
    
    if not search:

        print("Track List Empty")
    else:
        formatted_query = quote_plus(search)
        results = sp.search(formatted_query, limit=5)

        for result in results['tracks']['items']:
            db_track = Track.query.filter(Track.spotify_id == result['id']).all()
            print(db_track)

            if not (db_track):
                track_af = sp.audio_features(result['id'])
                new_track = Track(spotify_id=result['id'],
                                  name=result['name'],
                                  artist=result['artists'][0]['name'],
                                  album=result['album']['name'],
                                  acousticness=track_af[0]['acousticness'],
                                  danceability=track_af[0]['danceability'],
                                  duration_ms=track_af[0]['duration_ms'],
                                  energy=track_af[0]['energy'],
                                  instrumentalness=track_af[0]['instrumentalness'],
                                  key=track_af[0]['key'],
                                  liveness=track_af[0]['liveness'],
                                  loudness=track_af[0]['loudness'],
                                  mode=track_af[0]['mode'],
                                  speechiness=track_af[0]['speechiness'],
                                  tempo=track_af[0]['tempo'],
                                  time_signature=track_af[0]['time_signature'],
                                  valence=track_af[0]['valence'])

                db.session.add(new_track)
                tracks.append(new_track)

            # else:
            #     print(db_track)
            #     track_af = sp.audio_features(result['id'])
            #     track_to_add = Track(spotify_id=result['id'],
            #                       name=result['name'],
            #                       artist=result['artists'][0]['name'],
            #                       album=result['album']['name'],
            #                       acousticness=track_af[0]['acousticness'],
            #                       danceability=track_af[0]['danceability'],
            #                       duration_ms=track_af[0]['duration_ms'],
            #                       energy=track_af[0]['energy'],
            #                       instrumentalness=track_af[0]['instrumentalness'],
            #                       key=track_af[0]['key'],
            #                       liveness=track_af[0]['liveness'],
            #                       loudness=track_af[0]['loudness'],
            #                       mode=track_af[0]['mode'],
            #                       speechiness=track_af[0]['speechiness'],
            #                       tempo=track_af[0]['tempo'],
            #                       time_signature=track_af[0]['time_signature'],
            #                       valence=track_af[0]['valence'])

            #     tracks.append(track_to_add)


        db.session.commit()

    for x in range(len(tracks)):
        print (tracks[x])

    return render_template('search.html', tracks=tracks)

@app.route("/categories")
def show_af_categories():


    return render_template('af-categories.html')

@app.errorhandler(404)
def page_not_found(e):
    """404 NOT FOUND page."""

    return render_template('404.html'), 404