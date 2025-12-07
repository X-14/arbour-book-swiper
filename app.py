# app.py

from flask import Flask, render_template, request, jsonify, url_for
import joblib
import pandas as pd
import numpy as np
import sys
import os

from firebase_dal import get_user_swipes, add_user_swipe, get_user_preferences, get_user_liked_book_ids

# --- CONFIGURATION ---
app = Flask(__name__)

# --- LOAD AI MODEL ---
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sim_matrix_path = os.path.join(base_dir, 'models/similarity_matrix.joblib')
    book_data_path = os.path.join(base_dir, 'models/book_data_processed.joblib')

    if not os.path.exists(sim_matrix_path) or not os.path.exists(book_data_path):
        print(f"FATAL: Model files not found at {sim_matrix_path} or {book_data_path}. Run train_model.py first.")
        sys.exit(1)
        
    COSINE_SIM = joblib.load(sim_matrix_path)
    BOOK_DATA = joblib.load(book_data_path)
    print("AI Model loaded successfully.")
except Exception as e:
    print(f"FATAL: Error loading model files: {e}")
    sys.exit(1)

# --- AI RECOMMENDATION LOGIC ---
def get_recommendation_from_model(current_book_id, history_list):
    """Finds the next unread book most similar to the current one."""
    
    current_book_id = str(current_book_id)
    if current_book_id not in BOOK_DATA.index:
        current_book_id = BOOK_DATA.index[0] 

    idx = BOOK_DATA.index.get_loc(current_book_id)
    sim_scores = list(enumerate(COSINE_SIM[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    for i, score in sim_scores[1:]: 
        rec_id = BOOK_DATA.index[i]
        
        if str(rec_id) not in history_list:
            recommended_book = BOOK_DATA.loc[rec_id]
            
            return {
                'book_id': str(rec_id),
                'title': recommended_book['title'],
                'description': recommended_book['description'], 
                'image_url': recommended_book['image_url'],
                'score': float(score),
                'author': recommended_book.get('author', 'Unknown Author')
            }
            
    return {'book_id': 'DONE', 'title': 'No More Recommendations!', 'description': 'You have swiped all related books.', 'image_url': ''}, 200

def get_initial_book(user_genres, history_list):
    """Finds a starting book based on user genres."""
    # Filter books by genre if genres are provided
    if user_genres:
        # This assumes BOOK_DATA has a 'genre' or similar column. 
        # If not, we might need to rely on a fallback or search.
        # Let's check if 'genre' exists in BOOK_DATA. 
        # If not, we'll just return the first book not in history.
        if 'genre' in BOOK_DATA.columns:
             # Simple check: is any of the user's genres in the book's genre string?
             # This is a bit loose but works for a prototype.
             mask = BOOK_DATA['genre'].apply(lambda x: any(g.lower() in str(x).lower() for g in user_genres))
             genre_books = BOOK_DATA[mask]
             
             for book_id in genre_books.index:
                 if str(book_id) not in history_list:
                     book = genre_books.loc[book_id]
                     return {
                        'book_id': str(book_id),
                        'title': book['title'],
                        'description': book['description'], 
                        'image_url': book['image_url'],
                        'score': 'Based on your preferences',
                        'author': book.get('author', 'Unknown Author')
                    }

    # Fallback: Return first book not in history
    for book_id in BOOK_DATA.index:
        if str(book_id) not in history_list:
            book = BOOK_DATA.loc[book_id]
            return {
                'book_id': str(book_id),
                'title': book['title'],
                'description': book['description'], 
                'image_url': book['image_url'],
                'score': 'Start Swiping',
                'author': book.get('author', 'Unknown Author')
            }
            
    return {'book_id': 'DONE', 'title': 'No More Recommendations!', 'description': 'You have swiped all related books.', 'image_url': ''}, 200


# --- FLASK ROUTES ---

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login")
def login():
    return render_template('index.html') 

@app.route("/signup")
def signup():
    return render_template('signup.html')

@app.route("/home")
def home():
    return render_template('homepage.html')

@app.route("/preferences")
def preferences():
    return render_template('preferences.html')

@app.route("/isbn")
def isbn():
    return render_template('isbn.html')

@app.route("/recommendation")
def recommendation():
    # We need the user_id to fetch preferences. 
    # Since this is a standard GET request, we might need to rely on a query param 
    # or handle the initial fetch via AJAX in the frontend if we want to be purely client-side auth driven.
    # However, to make it "work" with the current structure where the template is rendered server-side:
    # We can render a "loading" state or a generic book, and then have the frontend immediately fetch the correct one?
    # OR, we can accept a user_id query param.
    
    user_id = request.args.get('user_id')
    
    initial_book = None
    if user_id:
        history_list = get_user_swipes(user_id)
        user_prefs = get_user_preferences(user_id)
        user_genres = user_prefs.get('genres', []) if user_prefs else []
        initial_book = get_initial_book(user_genres, history_list)
    else:
        # Fallback if no user_id provided (e.g. direct access without param)
        # We'll just show the first book.
        initial_book_data = BOOK_DATA.iloc[0]
        initial_book = {
            'book_id': str(initial_book_data.name),
            'title': initial_book_data['title'],
            'description': initial_book_data['description'],
            'image_url': initial_book_data['image_url'],
            'score': 'Start Swiping',
            'author': initial_book_data.get('author', 'Unknown Author')
        }

    return render_template('recommendation.html', 
        initial_book_id=initial_book['book_id'], 
        initial_title=initial_book['title'],
        initial_description=initial_book['description'],
        initial_image=initial_book['image_url'], 
        initial_score=initial_book.get('score', ''),
        initial_author=initial_book.get('author', 'Unknown Author')
    )

@app.route('/api/swipe', methods=['POST'])
def handle_swipe():
    data = request.get_json()
    current_book_id = data.get('book_id')
    user_action = data.get('action') 
    user_id = data.get('user_id') 

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    # 1. PERSISTENCE: Save swipe
    add_user_swipe(user_id, current_book_id, user_action)

    # 2. FILTERING: Get history
    history_list = get_user_swipes(user_id)

    # 3. AI: Get next recommendation
    next_book_data = get_recommendation_from_model(current_book_id, history_list)
    
    return jsonify(next_book_data), 200

@app.route("/liked")
def liked():
    return render_template('liked.html')

@app.route("/search")
def search():
    return render_template('search.html')

@app.route('/api/liked_books', methods=['GET'])
def get_liked_books():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    # Get liked book IDs
    liked_ids = get_user_liked_book_ids(user_id)
    
    liked_books = []
    for book_id in liked_ids:
        # Look up in BOOK_DATA
        if str(book_id) in BOOK_DATA.index:
            book = BOOK_DATA.loc[str(book_id)]
            liked_books.append({
                'book_id': str(book_id),
                'title': book['title'],
                'author': book.get('author', 'Unknown'),
                'image_url': book['image_url'],
                'description': book['description']
            })
            
    return jsonify(liked_books), 200

@app.route('/api/search', methods=['GET'])
def search_books():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])
    
    # Search in BOOK_DATA
    # We'll search title and author
    results = []
    
    # Create a mask for search
    mask = (BOOK_DATA['title'].str.lower().str.contains(query, na=False)) | \
           (BOOK_DATA['author'].str.lower().str.contains(query, na=False))
           
    matches = BOOK_DATA[mask].head(20) # Limit to 20 results
    
    for book_id, book in matches.iterrows():
        results.append({
            'book_id': str(book_id),
            'title': book['title'],
            'author': book.get('author', 'Unknown'),
            'image_url': book['image_url'],
            'description': book['description']
        })
        
    return jsonify(results), 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)