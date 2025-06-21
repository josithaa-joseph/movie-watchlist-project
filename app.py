from flask import Flask, render_template, request, redirect, flash, url_for
import requests
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# import secrets
# app.secret_key = secrets.token_hex(16)  # Generates a 32-character random hex string

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///watchlist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(10))
    poster = db.Column(db.String(200))
    imdb_id = db.Column(db.String(20), unique=True)
    rating = db.Column(db.Integer)
    watched = db.Column(db.Boolean, default=False)

# Create tables (run once)
with app.app_context():
    db.create_all()



# Homepage route
@app.route('/')
def home():
    return render_template('home.html')

# Search route (calls OMDB API)
@app.route('/search')
def search():
    query = request.args.get('q')
    if query:
        api_key = os.getenv('OMDB_API_KEY')
        url = f"http://www.omdbapi.com/?s={query}&apikey={api_key}"
        response = requests.get(url).json()
        # print(response)  # Debugging - check the actual API response
        movies = response.get('Search', [])  # Changed 'results' to 'Search'
        return render_template('search.html', movies=movies)
    return render_template('search.html', movies=[])

# Watchlist Page Route
@app.route('/add_to_watchlist', methods=['POST'])
def add_to_watchlist():
    try:
        # Get data from form
        movie_data = {
            'title': request.form.get('Title'),
            'year': request.form.get('Year'),
            'poster': request.form.get('Poster'),
            'imdb_id': request.form.get('imdbID')
        }
        
        if not all(movie_data.values()):
            raise ValueError("Missing form data")
        
        # Check if movie already exists
        if not Movie.query.filter_by(imdb_id=movie_data['imdb_id']).first():
            new_movie = Movie(
                title=movie_data['title'],
                year=movie_data['year'],
                poster=movie_data['poster'],
                imdb_id=movie_data['imdb_id']
            )
            db.session.add(new_movie)
            db.session.commit()
        
        return redirect('/watchlist')
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
        return redirect('/')

@app.route('/watchlist')
def watchlist():
    movies = Movie.query.all()
    # print("\n📦 MOVIES IN DATABASE:", movies)  # Debug print
    return render_template('watchlist.html', movies=movies)

@app.route('/delete/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect('/watchlist')

@app.route('/rate/<int:movie_id>', methods=['POST'])
def rate_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # Find the movie or show 404 error
    
    # Get the rating from the form (convert to integer)
    rating = request.form.get('rating')
    if rating and rating.isdigit():
        movie.rating = int(rating)
    else:
        movie.rating = None  # No rating selected
    
    db.session.commit()  # Save changes to database
    
    return redirect('/watchlist')  # Go back to watchlist

@app.route('/toggle_watched/<int:movie_id>', methods=['POST'])
def toggle_watched(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    movie.watched = not movie.watched  # This toggles the status
    db.session.commit()

    status = "watched" if movie.watched else "unwatched"
    flash(f"Marked '{movie.title}' as {status}!", "success")
    
    return redirect('/watchlist')

@app.route('/debug_db')
def debug_db():
    movies = Movie.query.all()
    return {
        'total_movies': len(movies),
        'movies': [{'title': m.title, 'id': m.id} for m in movies]
    }

if __name__ == '__main__':
    app.run(debug=True)