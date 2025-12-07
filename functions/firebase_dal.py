# firebase_dal.py

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import sys
import os

# --- INITIALIZE FIREBASE ---
try:
    # Use absolute path relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "serviceAccountKey.json")
    
    if os.path.exists(key_path):
        cred = credentials.Certificate(key_path)
        print(f"Using service account key from {key_path}")
    else:
        cred = credentials.ApplicationDefault()
        print("Using Application Default Credentials")

    # Check if app is already initialized to avoid re-initialization error
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase connected successfully.")
except Exception as e:
    print(f"FATAL ERROR: Failed to connect to Firebase. Error: {e}")
    # We don't exit here because in Cloud Functions it might just log the error and retry
    # sys.exit(1) 

# --- FIREBASE DATA FUNCTIONS ---

def get_all_books_from_db():
    """
    Fetches all documents from the 'books' collection.
    - Uses the ISBN (document ID) as 'book_id'.
    - Renames 'synopsis' to 'description' and 'coverimage' to 'image_url'.
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
        
        # 3. RENAME: Change 'coverimage' to 'image_url' for the Flask app
        if 'coverimage' in book_data:
            book_data['image_url'] = book_data.pop('coverimage')
        
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