import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from sqlalchemy import distinct
from forms import *
from model import db, Show, Venue, Artist

# App Config.
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
def init_db():
    db.init_app(app)
    db.app = app
    db.create_all()


migrate = Migrate(app, db)
init_db()

def format_datetime(value, format ='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)

def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    try:
        fcity_state = db.session.query(distinct(Venue.city), Venue.state).all()# format (city, state)
        for places in fcity_state:
            city, state = places[0], places[1]
            listed_data = {"city": city, "state": state, "venues": []}
            venues = Venue.query.filter_by(city=city, state=state).all()
            for venue in venues:
                upcoming_shows = [Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).all()]
                venue_data = {"id": venue.id, "name": venue.name, "num_upcoming_shows": len(upcoming_shows)}
                listed_data["venues"].append(venue_data)
            data.append(listed_data)
    except:
        db.session.rollback()
        flash("An error has occurred while loading the Venues")
        return render_template("pages/home.html")
    finally:
        return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search = "%{}%".format(request.form["search_term"])
    result_q = Venue.query.filter(Venue.name.ilike(f'%{search}%')).all()
    response={}
    response['count'] = len(result_q)
    response['data'] = result_q
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', '') )


def format_json(x):
    for i in ['[', ']', '{', '}', '"']:
        x = x.replace(i,'')
    return x.split(',')


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    shows = Show.query.filter_by(venue_id=venue_id)
    past_shows = []
    for show in shows.filter(Show.start_time < datetime.now()).all():
        artist = Artist.query.get(show.artist_id)
        response = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str( show.start_time),
        }
        past_shows.append(response)

    upcoming_shows = []
    for show in shows.filter(Show.start_time > datetime.now()).all():
        artist = Artist.query.get(show.artist_id)
        response = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
        }
        upcoming_shows.append(response)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": format_json(venue.genres),
        "address": venue.address,
        "city": venue.city,
        "state": venue.city,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "image_link": venue.image_link,
        "upcoming_shows": upcoming_shows,
        "past_shows": past_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    if form.validate():
        try:
            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            address = request.form['state']
            phone = request.form['phone']
            image_link = request.form['image_link']
            facebook_link = request.form['facebook_link']
            genres = json.dumps(request.form.getlist('genres'))
            website = request.form['website']
            seeking_talent = True if request.form['seeking_talent'] == 'True' else False
            seeking_description = request.form['seeking_description']
            venue = Venue(name=name, genres=genres, city=city, state=state, address=address,
                          phone=phone, website=website,
                          seeking_talent=seeking_talent, seeking_description=seeking_description,
                          facebook_link=facebook_link, image_link=image_link)
            db.session.add(venue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
        return render_template('pages/home.html')
    else:
        flash_errors(form)
        return redirect(url_for('create_venue_form', form=form))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id).first()
        db.session.delete(venue)
        db.session.commit()
        flash('Venue was successfully DELETED  ')
    except:
        db.session.rollback()
        flash('An error occurred')
    finally:
        db.session.close()
        return url_for("index")

#  Artists

@app.route('/artists')
def artists():
    return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():
    tag = request.form["search_term"]
    search = "%{}%".format(tag)
    result_q = Artist.query.filter(Artist.name.ilike(f'%{search}%')).all()
    response = {}
    response['count'] = len(result_q)
    response['data'] = result_q
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    query = db.session.query(Show).join(Artist, Artist.id == artist_id).join(Venue, Venue.id == Show.venue_id).all()
    past_shows, upcoming_shows = [], []

    for show in query:
        if show.start_time > datetime.now():
            response = {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": str(show.start_time)}
            past_shows.append(response)
        else:
             response = {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "venue_image_link": show.venue.image_link,
                "start_time": str(show.start_time)}
             upcoming_shows.append(response)

        data = {
            "id": artist_id,
            "name": show.artist.name,
            "city": show.artist.city,
            "state": show.artist.state,
            "phone": show.artist.phone,
            "website": show.artist.website,
            "facebook_link": show.artist.facebook_link,
            "seeking_venue": show.artist.seeking_venue,
            "seeking_description": show.artist.seeking_description,
            "image_link": show.artist.image_link,
            "upcoming_shows": upcoming_shows,
            "past_shows": past_shows,
            "past_shows_count": len(past_shows),
             "upcoming_shows_count": len(upcoming_shows),}

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.facebook_link.data = artist.facebook_link
    form.state.data = artist.state
    form.image_link.data = artist.image_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    if form.validate():
        try:
            artist = Artist.query.get(artist_id)
            artist.name = request.form['name']
            artist.genres = json.dumps(request.form.getlist('genres'))
            artist.city = request.form['city']
            artist.state = request.form['state']
            artist.phone = request.form['phone']
            artist.website = request.form['website']
            artist.facebook_link = request.form['facebook_link']
            artist.seeking_venue = True if request.form['seeking_venue'] == 'True' else False
            artist.seeking_description = request.form['seeking_description']
            artist.image_link = request.form['image_link']
            db.session.add(artist)
            db.session.commit()
        except:
            db.session.rollback()
            flash('An error occurred edit venues' + str(artist_id))
        finally:
            db.session.close()
            return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        flash_errors(form)
        return redirect(url_for('edit_artist', form=form))



@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.facebook_link.data = venue.facebook_link
    form.state.data = venue.state
    form.image_link.data = venue.image_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    if form.validate():
        try:
            venue = Venue.query.get(venue_id)
            venue.name = request.form['name']
            venue.city = request.form['city']
            venue.state = request.form['state']
            venue.genres = json.dumps(request.form.getlist('genres'))
            venue.address = request.form['address']
            venue.phone = request.form['phone']
            venue.facebook_link = request.form['facebook_link']
            venue.website = request.form['website']
            venue.image_link = request.form['image_link']
            db.session.add(venue)
            db.session.commit()
        except:
            db.session.rollback()
            flash('An error occurred edit venues' + str(venue_id))
        finally:
            db.session.close()
        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        flash_errors(form)
        return redirect(url_for('edit_venue', form=form))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)



@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    if form.validate():
        try:
            name = request.form['name']
            city = request.form['city']
            state = request.form['state']
            phone = request.form['phone']
            facebook_link = request.form['facebook_link']
            seeking_venue = True if request.form['seeking_venue'] == 'True' else False
            seeking_description = request.form['seeking_description']
            website = request.form['website']
            image_link = request.form['image_link']
            genres = request.form['genres']
            artist = Artist(name=name, city=city, state=state, phone=phone, website=website
                                , genres=genres, facebook_link=facebook_link, seeking_venue=seeking_venue
                                , seeking_description=seeking_description, image_link=image_link)
            db.session.add(artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        finally:
            db.session.close()
            return render_template('pages/home.html')
    else:
        flash_errors(form)
        return redirect(url_for('create_artist_form', form=form))




#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    response = []
    for show in Show.query.all():
        response.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
    return render_template('pages/shows.html', shows=response)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    if form.validate():
        try:
            show = Show(artist_id=int(request.form['artist_id']), venue_id=int(request.form['venue_id'])
                        , start_time=request.form['start_time'])
            db.session.add(show)
            db.session.commit()
            flash('Show was successfully listed!')

        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
        finally:
            db.session.close()
        return render_template('pages/home.html')
    else:
       flash_errors(form)
       return redirect(url_for('create_shows', form=form ))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')
# Launch.


# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
