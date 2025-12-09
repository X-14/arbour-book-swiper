# firebase_dal.py

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import sys
import os

# --- INITIALIZE FIREBASE ---
try:
    # Try to load from environment variable first (for Render deployment)
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS_JSON')
    
    if firebase_creds:
        # Use credentials from environment variable
        import json
        cred_dict = json.loads(firebase_creds)
        cred = credentials.Certificate(cred_dict)
        print("Firebase credentials loaded from environment variable.")
    else:
        # Fallback to local file (for local development)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        key_path = os.path.join(base_dir, "serviceAccountKey.json")
        cred = credentials.Certificate(key_path)
        print(f"Firebase credentials loaded from file: {key_path}")
    
    # Check if app is already initialized to avoid re-initialization error
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase connected successfully.")
except Exception as e:
    print(f"FATAL ERROR: Failed to connect to Firebase. Error: {e}")
    print("Ensure either:")
    print("  1. Environment variable FIREBASE_CREDENTIALS_JSON is set, OR")
    print("  2. File 'serviceAccountKey.json' exists in the project directory")
    sys.exit(1) 

# --- FIREBASE DATA FUNCTIONS ---

def get_all_books_from_db():
    """
    Fetches all documents from the 'books' collection.
    - Uses the ISBN (document ID) as 'book_id'.
    - Renames 'synopsis' to 'description' and maps image URLs to 'image_url'.
    """
    books_ref = db.collection('books')
    docs = books_ref.stream()
    
    book_list = []
    for doc in docs:
        book_data = doc.to_dict()
        
        # 1. Use the ISBN (Document ID) as the unique book_id
        book_data['book_id'] = doc.id
        
        # 2. RENAME: Change 'synopsis' to 'description' for the AI script
        if 'synopsis' in book_data:
            book_data['description'] = book_data.pop('synopsis')
        
        # 3. MAP IMAGE URL: Use 'coverImage' first, fallback to 'image', then set as 'image_url'
        image_url = ''
        if 'coverImage' in book_data:
            image_url = book_data.pop('coverImage')
        elif 'image' in book_data:
            image_url = book_data.pop('image')
        elif 'coverimage' in book_data:
            image_url = book_data.pop('coverimage')
        
        book_data['image_url'] = image_url
        
        book_list.append(book_data)
        
    return book_list

def get_user_swipes(user_id):
    """Fetches a list of book_ids (ISBNS) the user has already swiped."""
    # CRITICAL: Filters swipes based on the real user_id passed from app.py
    swipes_ref = db.collection('swipes').where('user_id', '==', user_id)
    swipes = swipes_ref.stream()
    
    return [swipe.to_dict()['book_id'] for swipe in swipes]

def add_user_swipe(user_id, book_id, action):
    """Saves a new swipe record ('like' or 'dislike')."""
    # CRITICAL: Stores the swipe using the real user_id passed from app.py
    db.collection('swipes').add({
        'user_id': user_id,
        'book_id': book_id,
        'action': action,
        'timestamp': datetime.now()
    })

def get_user_preferences(user_id):
    """Fetches user preferences from the 'users' collection."""
    user_ref = db.collection('users').document(user_id)
    doc = user_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

def get_user_liked_book_ids(user_id):
    """Fetches a list of book_ids that the user has LIKED."""
    swipes_ref = db.collection('swipes').where('user_id', '==', user_id).where('action', '==', 'like')
    swipes = swipes_ref.stream()
    
    return [swipe.to_dict()['book_id'] for swipe in swipes]

def save_user_preferences(user_id, age, genres, frequency):
    """Saves or updates user preferences in the 'users' collection."""
    user_ref = db.collection('users').document(user_id)
    user_ref.set({
        'age': age,
        'genres': genres,
        'frequency': frequency,
        'preferencesDone': True,
        'updatedAt': datetime.now()
    }, merge=True)
    return True