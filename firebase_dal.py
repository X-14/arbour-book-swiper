# firebase_dal.py

import firebase_admin
from firebase_admin import credentials, firestore, auth
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
    swipes = list(swipes_ref.stream())
    
    # Sort in Python to avoid Firestore Composite Index requirements for now
    # Assuming 'timestamp' exists; if not, it falls back to unsorted (or error, but timestamp is added on create)
    swipes.sort(key=lambda x: x.to_dict().get('timestamp', datetime.min), reverse=True)
    
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

def search_users(query):
    """
    Search for a user by email or username.
    1. Try Auth by email.
    2. Try Firestore 'users' collection by email field.
    3. Try Firestore 'users' collection by username field.
    """
    results = []
    seen_ids = set()
    
    # 1. Try Auth by Email (Exact match)
    try:
        user_record = auth.get_user_by_email(query)
        username = user_record.display_name or (user_record.email.split('@')[0] if user_record.email else "User")
        
        # Check profile
        user_doc = db.collection('users').document(user_record.uid).get()
        if user_doc.exists:
            d = user_doc.to_dict()
            username = d.get('username') or d.get('displayName') or username
            
        results.append({
            'user_id': user_record.uid,
            'username': username,
            'email': user_record.email
        })
        seen_ids.add(user_record.uid)
    except:
        pass # Not found in Auth or error
        
    # 2. Try Firestore 'users' collection (Exact email match if stored, or Username match)
    # Note: Firestore does not support OR matching across different fields easily in one query without a composite index or multiple queries.
    
    # Query by username (exact)
    try:
        q_user = db.collection('users').where('username', '==', query).stream()
        for doc in q_user:
            if doc.id in seen_ids:
                continue
            d = doc.to_dict()
            # We need email. It might not be in the doc (only in Auth), 
            # but we can try to fetch Auth user by UID to get email.
            email = d.get('email', 'Private Email')
            username = d.get('username', query)
            
            try:
                ur = auth.get_user(doc.id)
                email = ur.email
            except:
                pass
                
            results.append({
                'user_id': doc.id,
                'username': username,
                'email': email
            })
            seen_ids.add(doc.id)
    except Exception as e:
        print(f"Error searching Firestore by username: {e}")

    # Query by email field in Firestore (if we store it there, which we should start doing if not)
    # The current save_user_preferences doesn't strictly save email.
    
    return results

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
    
    # Pre-fetch user emails via auth? Or fetch one by one.
    # Requests are usually few. One by one is fine for now, but we can handle exceptions.
    
    for r in reqs:
        d = r.to_dict()
        d['id'] = r.id
        # Fetch sender info from Auth to ensure we get Email
        try:
            user_record = auth.get_user(d['from_uid'])
            d['sender_email'] = user_record.email
            d['sender_username'] = user_record.display_name or user_record.email
        except Exception as e:
            # Fallback to Firestore if Auth fails (rare) or just handle gracefully
            d['sender_email'] = "Unknown Email"
            d['sender_username'] = "Unknown User"
            
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
    Returns:
    1. Set of liked genres
    2. Dictionary of {book_id: [friend_email1, friend_email2]} for liked books.
    
    OPTIMIZED: Uses batch fetching.
    """
    all_genres = set()
    friends_likes_map = {} # book_id -> list of friend emails
    
    if not friend_ids:
        return [], {}
        
    users_ref = db.collection('users')
    
    # 1. Batch Get User Docs (for genres) AND Auth Users (for emails)
    
    # A. Get Emails from Auth (Batch)
    friend_emails = {}
    try:
        # auth.get_users takes a list of UidIdentifier
        identifiers = [auth.UidIdentifier(uid) for uid in friend_ids]
        get_users_result = auth.get_users(identifiers)
        
        for user_record in get_users_result.users:
            friend_emails[user_record.uid] = user_record.email
            
    except Exception as e:
        print(f"Error batch fetching users from Auth: {e}")
        # Fallback?
    
    # B. Get Genres from Firestore (Batch)
    refs = [users_ref.document(fid) for fid in friend_ids]
    user_docs = db.get_all(refs)
    
    for doc in user_docs:
        if not doc.exists:
            continue
        data = doc.to_dict()
        
        # Genres
        genres = data.get('genres', [])
        for g in genres:
            all_genres.add(g.lower())
            
    # 2. Batch Get Swipes (Likes)
    # "IN" query is limited to 30. We must chunk it.
    
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
            
    # Only fetch if we have friends
    if friend_ids:
        swipes_ref = db.collection('swipes')
        for chunk in chunks(friend_ids, 10): # Safe chunk size 10
             # Get all likes from these users
             q = swipes_ref.where('user_id', 'in', chunk).where('action', '==', 'like')
             docs = q.stream()
             
             for s in docs:
                 d = s.to_dict()
                 bid = d.get('book_id')
                 uid = d.get('user_id')
                 
                 # Use email if available, else fallback to something
                 f_email = friend_emails.get(uid, "A Friend")
                 
                 str_bid = str(bid)
                 if str_bid not in friends_likes_map:
                     friends_likes_map[str_bid] = []
                 # Avoid duplicates
                 if f_email not in friends_likes_map[str_bid]:
                     friends_likes_map[str_bid].append(f_email)
            
    return list(all_genres), friends_likes_map

def remove_user_swipe(user_id, book_id):
    """Removes a swipe (unlike)."""
    # Find the swipe document
    swipes = db.collection('swipes').where('user_id', '==', user_id).where('book_id', '==', str(book_id)).stream()
    
    deleted = False
    for swipe in swipes:
        swipe.reference.delete()
        deleted = True
        
    return deleted