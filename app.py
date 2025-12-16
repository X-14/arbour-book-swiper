# app.py

from flask import Flask, render_template, request, jsonify, url_for
import joblib
import pandas as pd
import numpy as np
import sys
import os

from firebase_dal import (
    get_user_swipes, add_user_swipe, get_user_preferences, 
    get_user_liked_book_ids, save_user_preferences, get_user_disliked_book_ids,
    search_users, send_friend_request, answer_friend_request,
    get_friend_requests, get_friends, get_friends_preferences_data, remove_user_swipe
)

# --- CONFIGURATION ---
app = Flask(__name__)

# --- LOAD AI MODEL ---
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sim_matrix_path = os.path.join(base_dir, 'models/similarity_matrix.joblib')
    book_data_path = os.path.join(base_dir, 'models/book_data_processed.joblib')

    if not os.path.exists(sim_matrix_path) or not os.path.exists(book_data_path):
        print(f"Model files not found. Attempting to train model...")
        import train_model
        success = train_model.train_model()
        if not success:
            print("FATAL: Model training failed on startup.")
            sys.exit(1)
            
    COSINE_SIM = joblib.load(sim_matrix_path)
    BOOK_DATA = joblib.load(book_data_path)
    
    # PRE-PROCESS OPTIMIZATION: Convert genres to lowercase string once
    BOOK_DATA['genres_str'] = BOOK_DATA['genres'].fillna('').astype(str).str.lower()
    
    print("AI Model loaded successfully.")
except Exception as e:
    print(f"FATAL: Error loading model files: {e}")
    sys.exit(1)

# --- AI RECOMMENDATION LOGIC ---

def calculate_preference_score(book, user_genres):
    """
    Calculate how well a book matches the user's preferences (0-1).
    Optimized to use pre-calculated 'genres_str'.
    """
    if not user_genres:
        return 0.0
    
    # Access pre-calc lowercase string directly
    book_genres_str = book.get('genres_str', '')
    if not book_genres_str:
         return 0.0

    # Assume user_genres are already lowercased by the caller or do it simply
    # (Doing it here 100s of times is minor compared to df operations but let's be safe)
    # We will assume caller passes valid list.
    
    # Count matches
    matches = 0
    for genre in user_genres:
        # Assuming user_genres passed in are already normalized or we do it cheaply
        if genre.lower() in book_genres_str:
            matches += 1
    
    return matches / len(user_genres)

def get_recommendations_sorted_by_preference(user_genres, history_list, limit=100):
    """
    Get books sorted by compatibility with user preferences.
    Returns a sorted list of (book_id, combined_score) tuples.
    """
    all_scores = []
    
    for book_id in BOOK_DATA.index:
        # Skip already swiped books
        if str(book_id) in history_list:
            continue
        
        book = BOOK_DATA.loc[book_id]
        
        # Calculate genre preference score (0-1)
        genre_score = calculate_preference_score(book, user_genres)
        
        # Get the average content similarity to all books (baseline relevance)
        idx = BOOK_DATA.index.get_loc(book_id)
        avg_similarity = COSINE_SIM[idx].mean()
        
        # Combined score: 70% genre match + 30% content similarity
        # This ensures books matching user preferences are prioritized
        combined_score = (genre_score * 0.7) + (avg_similarity * 0.3)
        
        all_scores.append((str(book_id), combined_score))
    
    # Sort by combined score (highest first)
    all_scores.sort(key=lambda x: x[1], reverse=True)
    
    return all_scores[:limit]

def get_recommendation_from_model(current_book_id, history_list, user_genres=None, liked_book_ids=None, disliked_book_ids=None, friends_genres=None, friends_likes_map=None):
    """
    Finds the next unread book.
    Returns dict including 'liked_by' if applicable.
    """
    current_book_id = str(current_book_id)
    
    if current_book_id not in BOOK_DATA.index:
        current_book_id = BOOK_DATA.index[0]
    
    idx = BOOK_DATA.index.get_loc(current_book_id)
    sim_scores = list(enumerate(COSINE_SIM[idx]))
    
    # Pre-process liked data for fast lookup
    liked_authors = set()
    liked_titles = []
    if liked_book_ids:
        valid_ids = [bid for bid in liked_book_ids if bid in BOOK_DATA.index]
        if valid_ids:
            liked_authors = set(BOOK_DATA.loc[valid_ids]['author'].fillna('').str.lower().tolist())
            liked_titles = BOOK_DATA.loc[valid_ids]['title'].fillna('').str.lower().tolist()
            
    # Pre-process disliked data
    disliked_authors = set()
    disliked_titles = []
    if disliked_book_ids:
        valid_bad_ids = [bid for bid in disliked_book_ids if bid in BOOK_DATA.index]
        if valid_bad_ids:
            disliked_authors = set(BOOK_DATA.loc[valid_bad_ids]['author'].fillna('').str.lower().tolist())
            disliked_titles = BOOK_DATA.loc[valid_bad_ids]['title'].fillna('').str.lower().tolist()

    # Enhanced Scoring Logic
    enhanced_scores = []
    
    # OPTIMIZATION: Use numpy argsort for speed instead of converting to list and sorting
    # We want top 500 most similar. 
    # argsort returns indices of sorted array (ascending). We take the last 500 and reverse.
    top_indices = COSINE_SIM[idx].argsort()[-500:][::-1]

    for rec_idx in top_indices:
        # Get the actual book ID from the index
        rec_id = BOOK_DATA.index[rec_idx]
        content_sim = COSINE_SIM[idx][rec_idx]
        
        # Skip current book and already swiped books
        if str(rec_id) in history_list or rec_idx == idx:
            continue
        
        book = BOOK_DATA.loc[rec_id]
        
        # 1. Base Score: Content Similarity (Weight: 40%)
        score = content_sim * 0.4
        
        # 2. Preference Score: Genre Match (Weight: 40%)
        if user_genres:
            genre_score = calculate_preference_score(book, user_genres)
            score += genre_score * 0.4
        
        # 3. Boost: Liked Author (+10%)
        book_author = book.get('author', '').lower()
        if book_author in liked_authors:
            score += 0.1
            
        # 4. Boost: Series/Title Similarity (+15%)
        title_lower = book['title'].lower()
        if len(title_lower) > 5:
            for l_title in liked_titles:
                if len(l_title) > 5 and (l_title in title_lower or title_lower in l_title):
                    score += 0.15
                    break
                    
        # 5. PENALTY: Disliked Author (-15%)
        if book_author in disliked_authors:
            score -= 0.15
            
        if len(title_lower) > 5:
            for d_title in disliked_titles:
                 if len(d_title) > 5 and (d_title in title_lower or title_lower in d_title):
                    score -= 0.10
                    break
        
        # 7. Boost: Friend Recommendations (+10%)
        # If a friend liked this book
        liked_by_list = []
        if friends_likes_map and str(rec_id) in friends_likes_map:
             score += 0.15 # Increased boost
             liked_by_list = friends_likes_map[str(rec_id)]
             
        # 8. Boost: Friend Genre Match (+5%)
        if friends_genres:
            f_genre_score = calculate_preference_score(book, friends_genres)
            score += f_genre_score * 0.05
                    
        enhanced_scores.append((rec_id, score, liked_by_list))
    
    # Sort by final enhanced score
    enhanced_scores.sort(key=lambda x: x[1], reverse=True)
    
    if enhanced_scores:
        rec_id, score, liked_by_list = enhanced_scores[0]
        recommended_book = BOOK_DATA.loc[rec_id]
        
        final_score = max(0.0, min(score * 100, 100.0))
        
        return {
            'book_id': str(rec_id),
            'title': recommended_book['title'],
            'description': recommended_book['description'],
            'image_url': recommended_book['image_url'],
            'score': final_score,
            'author': recommended_book.get('author', 'Unknown Author'),
            'liked_by': liked_by_list
        }
    
    return {'book_id': 'DONE', 'title': 'No More Recommendations!', 'description': 'You have swiped all related books.', 'image_url': '', 'score': 0, 'liked_by': []}

def get_initial_book(user_genres, history_list):
    """
    Finds the best starting book based on user preferences.
    Books are sorted by compatibility with user's genre preferences.
    """
    # NOTE: Does not currently use liked_books for the very first book to keep it fast/simple,
    # but subsequent swipes will use the full logic.
    if user_genres:
        # Get all books sorted by preference match
        sorted_recommendations = get_recommendations_sorted_by_preference(user_genres, history_list)
        
        if sorted_recommendations:
            best_book_id, score = sorted_recommendations[0]
            book = BOOK_DATA.loc[best_book_id]
            
            return {
                'book_id': str(best_book_id),
                'title': book['title'],
                'description': book['description'],
                'image_url': book['image_url'],
                'score': f'{score * 100:.1f}% Match',
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
    
    return {'book_id': 'DONE', 'title': 'No More Recommendations!', 'description': 'You have swiped all books.', 'image_url': '', 'score': 0}



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

    initial_liked_by_text = ""
    if user_id and initial_book:
        # Fetch friend likes for the initial book to display immediately
        friends_list = get_friends(user_id)
        if friends_list:
            friends_genres, friends_likes_map = get_friends_preferences_data(friends_list)
            if friends_likes_map and initial_book['book_id'] in friends_likes_map:
                liked_emails = friends_likes_map[initial_book['book_id']]
                initial_liked_by_text = "Liked by: " + ", ".join(liked_emails)

    return render_template('recommendation.html', 
        initial_book_id=initial_book['book_id'], 
        initial_title=initial_book['title'],
        initial_description=initial_book['description'],
        initial_image=initial_book['image_url'], 
        initial_score=initial_book.get('score', ''),
        initial_author=initial_book.get('author', 'Unknown Author'),
        initial_liked_by=initial_liked_by_text
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
    
    # 3. GET USER PREFERENCES
    user_prefs = get_user_preferences(user_id)
    user_genres = user_prefs.get('genres', []) if user_prefs else []

    # 4. GET LIKED BOOKS (for Author/Series matching)
    liked_book_ids = get_user_liked_book_ids(user_id)
    
    # 5. GET DISLIKED BOOKS (for Penalties)
    disliked_book_ids = get_user_disliked_book_ids(user_id)

    # 6. GET FRIENDS DATA
    friends_list = get_friends(user_id)
    friends_genres, friends_likes_map = get_friends_preferences_data(friends_list) if friends_list else ([], {})

    # 7. AI: Get next recommendation
    next_book_data = get_recommendation_from_model(current_book_id, history_list, user_genres, liked_book_ids, disliked_book_ids, friends_genres, friends_likes_map)
    
    return jsonify(next_book_data), 200

@app.route("/liked")
def liked():
    return render_template('liked.html')

@app.route("/search")
def search():
    return render_template('search.html')

@app.route("/friends")
def friends():
    return render_template('friends.html')

# --- FRIENDS API ---

@app.route('/api/users/search', methods=['GET'])
def search_users_api():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    # Assuming query is email
    results = search_users(query)
    # If no email match, maybe try fallback to username search? 
    # For now, stick to email as requested.
    return jsonify(results)

@app.route('/api/friends/request', methods=['POST'])
def send_request_api():
    data = request.get_json()
    from_uid = data.get('from_uid')
    to_uid = data.get('to_uid')
    
    if not from_uid or not to_uid:
        return jsonify({'error': 'Missing user IDs'}), 400
        
    success, msg = send_friend_request(from_uid, to_uid)
    if success:
        return jsonify({'message': msg}), 200
    else:
        return jsonify({'error': msg}), 400

@app.route('/api/friends/respond', methods=['POST'])
def respond_request_api():
    data = request.get_json()
    request_id = data.get('request_id')
    status = data.get('status') # 'accepted' or 'rejected'
    
    if not request_id or status not in ['accepted', 'rejected']:
        return jsonify({'error': 'Invalid request'}), 400
        
    answer_friend_request(request_id, status)
    return jsonify({'success': True}), 200

@app.route('/api/friends', methods=['GET'])
def get_friends_data():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
        
    friends = get_friends(user_id)
    requests = get_friend_requests(user_id)
    
    # Enrich friend data with names (we need to fetch them)
    # Ideally DAL should handle this but we'll do quick enrichment here or DAL
    # Let's trust DAL gave us IDs, we need names.
    # Actually, for MVP, we need names. 
    # Let's assume frontend will fetch details or we update DAL to return objects.
    # The DAL `get_friends` returns IDs. We should probably update it to return objects or fetch here.
    # Let's Update DAL or fetch here.
    # fetching here...
    
    friend_details = []
    # This loop is inefficient but fine for MVP (<100 friends)
    # This loop is inefficient but fine for MVP (<100 friends)
    from firebase_dal import db, auth # Need DB and Auth access
    users_ref = db.collection('users')
    
    for fid in friends:
        doc = users_ref.document(fid).get()
        if doc.exists:
            d = doc.to_dict()
            
            # Fetch friend's liked books
            liked_ids = get_user_liked_book_ids(fid)
            top_books = []
            
            # Get details for up to 3 liked books
            valid_ids = [bid for bid in liked_ids if str(bid) in BOOK_DATA.index]
            recent_likes = valid_ids[:3] if valid_ids else [] 
            
            for bid in recent_likes:
                book = BOOK_DATA.loc[str(bid)]
                top_books.append({
                    'title': book['title'],
                    'image_url': book['image_url']
                })
            
            # Fetch email from Auth
            email = "Unknown Email"
            try:
                ur = auth.get_user(fid)
                email = ur.email
            except:
                pass

            # Determine display name
            raw_name = d.get('username') or d.get('displayName')
            display_name = raw_name
            
            if not display_name or display_name == 'Unknown':
                if email and '@' in email:
                    display_name = email.split('@')[0]
                else:
                    display_name = "Friend"

            friend_details.append({
                'user_id': fid, 
                'username': display_name,
                'email': email,
                'top_books': top_books
            })
            
    return jsonify({
        'friends': friend_details,
        'requests': requests
    })

@app.route('/api/unlike', methods=['POST'])
def unlike_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    
    if not user_id or not book_id:
        return jsonify({'error': 'Missing data'}), 400
        
    success = remove_user_swipe(user_id, book_id)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Swipe not found'}), 404

def calculate_book_score(book, user_genres, liked_authors=None, liked_titles=None, avg_similarity=0.1):
    """
    Unified scoring function for both recommendations and liked books display.
    """
    # 1. Base Score (40%)
    score = avg_similarity * 0.4
    
    # 2. Preference Score: Genre Match (40%)
    if user_genres:
        genre_score = calculate_preference_score(book, user_genres)
        score += genre_score * 0.4
    
    # 3. Boost: Liked Author (15%)
    # If the book itself is in the liked list (which it is for this page), 
    # it naturally matches its own author, but we validly want to show that high score.
    book_author = book.get('author', '').lower()
    if liked_authors and book_author in liked_authors:
        score += 0.15
        
    # 4. Boost: Series/Title Similarity (15%)
    title_lower = book['title'].lower()
    if liked_titles and len(title_lower) > 5:
        for l_title in liked_titles:
            # Avoid self-match comparison for exact strictness if needed, 
            # but for "why do I like this", high score is good.
            if len(l_title) > 5 and (l_title in title_lower or title_lower in l_title):
                score += 0.15
                break
                
    return score

@app.route('/api/liked_books', methods=['GET'])
def get_liked_books():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    # Get user preferences for scoring
    user_prefs = get_user_preferences(user_id)
    user_genres = user_prefs.get('genres', []) if user_prefs else []
    
    # Get liked book IDs
    liked_ids = get_user_liked_book_ids(user_id)
    
    # Pre-process liked data for context
    liked_authors = set()
    liked_titles = []
    
    # We first need to check validity of indices
    valid_ids = [str(bid) for bid in liked_ids if str(bid) in BOOK_DATA.index]
    
    if valid_ids:
        liked_authors = set(BOOK_DATA.loc[valid_ids]['author'].fillna('').str.lower().tolist())
        liked_titles = BOOK_DATA.loc[valid_ids]['title'].fillna('').str.lower().tolist()
    
    liked_books = []
    for book_id in valid_ids:
        book = BOOK_DATA.loc[book_id]
        
        # Calculate score consistent with recommendation engine
        # We use a default avg_similarity since calculating it per book is expensive O(N^2)
        # But we can grab the pre-calculated row mean if available, or just estimate.
        # For accuracy, we'll try to get the row mean.
        idx = BOOK_DATA.index.get_loc(book_id)
        avg_sim = COSINE_SIM[idx].mean() if idx < len(COSINE_SIM) else 0.1
        
        raw_score = calculate_book_score(book, user_genres, liked_authors, liked_titles, avg_sim)
        
        # ARTIFICIAL BOOST: Multiply by 2.0 to normalize visualization to a "Match%" scale users expect.
        # Since avg_sim is low (0.1-0.3), raw scores are often 0.3-0.5. This maps them to 60-100%.
        final_score = max(0.0, min(raw_score * 2.0 * 100, 100.0))
        
        liked_books.append({
            'book_id': str(book_id),
            'title': book['title'],
            'author': book.get('author', 'Unknown'),
            'image_url': book['image_url'],
            'description': book['description'],
            'score': f"{final_score:.1f}% Match"
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
        
    return jsonify(results)

@app.route('/api/explore', methods=['GET'])
def explore_books():
    """
    Get 3 recommendations that are OUTSIDE the user's preferred genres.
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify([])
        
    history_list = get_user_swipes(user_id)
    user_prefs = get_user_preferences(user_id)
    user_genres = user_prefs.get('genres', []) if user_prefs else []
    
    # Normalize user genres for exclusion
    user_genres_lower = set(g.lower() for g in user_genres)
    
    explore_results = []
    
    # We want high quality books (likely popular or high similarity to avg) 
    # but strictly NOT in the user's genre list.
    
    for book_id in BOOK_DATA.index:
        if str(book_id) in history_list:
            continue
            
        book = BOOK_DATA.loc[book_id]
        book_genres_str = str(book.get('genres', '')).lower()
        
        # Check if book intersects with ANY user genre
        has_overlap = any(ug in book_genres_str for ug in user_genres_lower)
        
        if not has_overlap:
             # This book is "Different". 
             # We rank by general content popularity/similarity to ensure quality.
             idx = BOOK_DATA.index.get_loc(book_id)
             score = COSINE_SIM[idx].mean() # Use average similarity as a proxy for "centrality/quality"
             
             explore_results.append((book_id, score, book))
             
    # Sort by score descending
    explore_results.sort(key=lambda x: x[1], reverse=True)
    
    # Return top 3
    final_output = []
    for book_id, score, book in explore_results[:3]:
        # Normalize score for display (similar to other endpoints)
        # Explore scores are just raw cosine mean (0.0-1.0 typically low 0.1-0.3)
        # We'll apply a visual boost for the user "Match" feeling.
        display_score = f"{min(score * 3.0 * 100, 98.0):.1f}% Match" 
        
        final_output.append({
            'book_id': str(book_id),
            'title': book['title'],
            'author': book.get('author', 'Unknown'),
            'image_url': book['image_url'],
            'description': book['description'],
            'score': display_score
        })
        
    return jsonify(final_output), 200

@app.route('/api/save_preferences', methods=['POST'])
def save_preferences():
    """Save or update user preferences."""
    data = request.get_json()
    user_id = data.get('user_id')
    age = data.get('age')
    genres = data.get('genres', [])
    frequency = data.get('frequency')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    try:
        save_user_preferences(user_id, age, genres, frequency)
        return jsonify({'success': True, 'message': 'Preferences saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync_database', methods=['POST'])
def sync_database():
    """
    Sync Firebase data to in-memory BOOK_DATA.
    This endpoint should be called after adding/updating/deleting books in the admin interface.
    """
    global BOOK_DATA, COSINE_SIM
    
    try:
        from firebase_dal import get_all_books_from_db
        
        print("Syncing database from Firebase...")
        
        # 1. Fetch all books from Firebase
        raw_data = get_all_books_from_db()
        
        if not raw_data:
            return jsonify({'error': 'No book data found in Firebase'}), 400
        
        # 2. Convert to DataFrame
        df = pd.DataFrame(raw_data)
        print(f"Loaded {len(df)} records from Firebase.")
        
        # 3. Data Cleaning (same as train_model.py)
        required_cols = ['book_id', 'description', 'genres', 'title', 'image_url', 'author']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        
        df.dropna(subset=['book_id'], inplace=True)
        df['description'] = df['description'].fillna('')
        df['genres'] = df['genres'].fillna('')
        df['title'] = df['title'].fillna('Unknown Title')
        df['author'] = df['author'].fillna('Unknown')
        
        # Ensure book_id is the index
        df['book_id'] = df['book_id'].astype(str)
        df.set_index('book_id', inplace=True)
        
        # 4. Feature Engineering
        df['soup'] = df['title'] + ' ' + df['description'] + ' ' + df['genres']
        
        # 5. Regenerate similarity matrix
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import linear_kernel
        
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['soup'])
        cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
        
        # 6. Update global variables
        BOOK_DATA = df
        COSINE_SIM = cosine_sim
        
        # 7. Re-process optimization field
        BOOK_DATA['genres_str'] = BOOK_DATA['genres'].fillna('').astype(str).str.lower()
        
        # 8. Save to disk for persistence
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(base_dir, 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            
        joblib.dump(COSINE_SIM, os.path.join(models_dir, 'similarity_matrix.joblib'))
        joblib.dump(BOOK_DATA, os.path.join(models_dir, 'book_data_processed.joblib'))
        
        print(f"Database synced successfully! {len(BOOK_DATA)} books now available.")
        
        return jsonify({
            'success': True, 
            'message': f'Database synced successfully. {len(BOOK_DATA)} books loaded.',
            'book_count': len(BOOK_DATA)
        }), 200
        
    except Exception as e:
        print(f"Error syncing database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to sync database: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)