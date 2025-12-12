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

def get_user_disliked_book_ids(user_id):
    """Fetches a list of book_ids that the user has DISLIKED."""
    swipes_ref = db.collection('swipes').where('user_id', '==', user_id).where('action', '==', 'dislike')
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

# --- FRIENDS SYSTEM ---

def search_users_by_username(query):
    """
    Search for users by displayName (username).
    Returns a list of {user_id, username}
    """
    users_ref = db.collection('users')
    # Note: Firestore doesn't support partial string match easily without third-party (Algolia).
    # We will fetch all users and filter in python (NOT SCALABLE for production, but okay for MVP).
    # Or rely on exact match. Let's try to match start of string.
    
    # We need to ensure text is queryable
    all_users = users_ref.stream()
    matches = []
    query = query.lower()
    
    for doc in all_users:
        data = doc.to_dict()
        # We assume we store displayName in 'users' collection. 
        # If not, we might need to rely on the client passing it or store it during login/preferences.
        # Let's assume we start storing 'username' or 'displayName' in users doc.
        
        username = data.get('username') or data.get('displayName', '')
        if username and query in username.lower():
            matches.append({
                'user_id': doc.id,
                'username': username
            })
    
    return matches[:10]

def send_friend_request(from_uid, to_uid):
    """Creates a pending friend request."""
    # Check if request already exists
    existing = db.collection('friendships').where('from_uid', '==', from_uid).where('to_uid', '==', to_uid).get()
    if existing:
        return False, "Request already sent."
    
    # Check reverse (if they are already friends or requested)
    reverse = db.collection('friendships').where('from_uid', '==', to_uid).where('to_uid', '==', from_uid).get()
    if reverse:
        return False, "User has already requested you or you are friends."

    db.collection('friendships').add({
        'from_uid': from_uid,
        'to_uid': to_uid,
        'status': 'pending',
        'timestamp': datetime.now()
    })
    return True, "Request sent."

def answer_friend_request(request_id, status):
    """Accept or reject a friend request. Status should be 'accepted' or 'rejected'."""
    ref = db.collection('friendships').document(request_id)
    if status == 'rejected':
        ref.delete()
    else:
        ref.update({'status': 'accepted'})
    return True

def get_friend_requests(user_id):
    """Get pending incoming requests."""
    reqs = db.collection('friendships').where('to_uid', '==', user_id).where('status', '==', 'pending').stream()
    results = []
    for r in reqs:
        d = r.to_dict()
        d['id'] = r.id
        # Fetch sender info
        sender = db.collection('users').document(d['from_uid']).get()
        if sender.exists:
            s_data = sender.to_dict()
            d['sender_username'] = s_data.get('username') or s_data.get('displayName', 'Unknown')
        results.append(d)
    return results

def get_friends(user_id):
    """Get list of active friends."""
    # Friends can be where user is from_uid OR to_uid, and status is accepted
    friends = []
    
    # Case 1: user sent request
    sent = db.collection('friendships').where('from_uid', '==', user_id).where('status', '==', 'accepted').stream()
    for f in sent:
        other_id = f.to_dict()['to_uid']
        friends.append(other_id)
        
    # Case 2: user received request
    received = db.collection('friendships').where('to_uid', '==', user_id).where('status', '==', 'accepted').stream()
    for f in received:
        other_id = f.to_dict()['from_uid']
        friends.append(other_id)
        
    return list(set(friends))

def get_friends_preferences_data(friend_ids):
    """
    Aggregate preferences and liked books from a list of friend IDs.
    Returns sets of liked genres and liked book IDs.
    """
    all_genres = set()
    all_liked_books = set()
    
    for fid in friend_ids:
        # Genres
        u_doc = db.collection('users').document(fid).get()
        if u_doc.exists:
            genres = u_doc.to_dict().get('genres', [])
            for g in genres:
                all_genres.add(g.lower())
                
        # Liked Books
        likes = get_user_liked_book_ids(fid)
        for bid in likes:
            all_liked_books.add(bid)
            
    return list(all_genres), list(all_liked_books)

def remove_user_swipe(user_id, book_id):
    """Removes a swipe (unlike)."""
    # Find the swipe document
    swipes = db.collection('swipes').where('user_id', '==', user_id).where('book_id', '==', str(book_id)).stream()
    
    deleted = False
    for swipe in swipes:
        swipe.reference.delete()
        deleted = True
        
    return deleted