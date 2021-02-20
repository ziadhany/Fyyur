# Models.
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class Venue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship("Show", backref="venue", lazy=True)

    def __repr__(self):
        return '<Venue: {}  - {} >'.format(self.id, self.name)


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500))
    city = db.Column(db.String(500))
    state = db.Column(db.String(500))
    phone = db.Column(db.String(500))
    genres = db.Column(db.String(500))
    website = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref="artist", lazy=True)

    def __repr__(self):
        return '<Artist: {}  - {} >'.format(self.id, self.name)


class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return '<Show: {}  - {}  >'.format(self.id, self.start_time)
