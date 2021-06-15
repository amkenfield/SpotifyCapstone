from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class Track(db.Model):
    """Individual track condensed and consolidated from Spotify's Track and AudioFeature objects."""

    __tablename__ = 'tracks'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    spotify_id = db.Column(
        db.Text,
        nullable=False
    )

    name = db.Column(
        # Should this be UnicodeText instead?
        db.Text,
        nullable=False
    )

    # Initially this will only take the first artist, if there are multiple
    # attributed - something to be improved/fixed for v.2 etc.
    # Also: this could/should be its own db table in future versions
    # (and thus relationships, etc.)
    artist = db.Column(
        db.Text,
        nullable=False
    )

    album = db.Column(
        db.Text,
        nullable=False
    )

    acousticness = db.Column(
        db.Float,
        nullable=False
    )

    danceability = db.Column(
        db.Float,
        nullable=False
    )

    duration_ms = db.Column(
        db.Integer,
        nullable=False
    )

    energy = db.Column(
        db.Float,
        nullable=False
    )

    instrumentalness = db.Column(
        db.Float,
        nullable=False
    )

    key = db.Column(
        db.Integer,
        nullable=False
    )

    liveness = db.Column(
        db.Float,
        nullable=False
    )

    loudness = db.Column(
        db.Float,
        nullable=False
    )

    mode = db.Column(
        db.Integer,
        nullable=False
    )

    speechiness = db.Column(
        db.Float,
        nullable=False
    )

    tempo = db.Column(
        db.Float,
        nullable=False
    )

    time_signature = db.Column(
        db.Integer,
        nullable=False
    )

    valence = db.Column(
        db.Float,
        nullable=False
    )

    ############## QUESTION ###############
    # I had named the backref 'tracks', trying(?) to follow the paradigm
    # given in the SQLAlchemy M2M lesson, but it would throw an error -
    # sqlalchemy.exc.ArgumentError: Error creating backref 'tracks' 
    # on relationship 'Track.users': property of that name exists 
    # on mapper 'mapped class User->users'
    # One, even after looking at SlackOverflow, I'm not totally sure why this is,
    # and Two, would there be a better name to give the backref than the one I'm using?
    # (Same situation applies in the User.tracks backref below)
    users = db.relationship('User',
                            secondary='users_tracks',
                            backref='own_tracks',
                            cascade="all, delete")

class User(db.Model):
    """User able to save tracks to their profile"""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # unsure if this would be needed, perhaps for acct recovery?
    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    tracks = db.relationship('Track',
                             secondary='users_tracks',
                             backref='track_users',
                             cascade="all, delete")

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_following(self, followed_track):
        """Is this user following 'track'?"""

        found_track_list = [track for track in self.tracks if track == followed_track]
        return len(found_track_list) == 1

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class UserTrack(db.Model):
    """Mapping of a user to a track"""

    __tablename__ = 'users_tracks'

    # id = db.Column(db.Integer,
    #                primary_key=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete="CASCADE"),
                        primary_key=True)

    track_id = db.Column(db.Integer,
                         db.ForeignKey('tracks.id', ondelete="CASCADE"),
                         primary_key=True)

def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)