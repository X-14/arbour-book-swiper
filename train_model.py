# train_model.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import joblib
import os
import sys

# --- Correctly import the function name ---
from firebase_dal import get_all_books_from_db 

def train_model():
    if not os.path.exists('models'):
        os.makedirs('models')

    print("--- Starting AI Model Training (Source: Firebase) ---")

    try:
        # 1. Data Acquisition
        raw_data = get_all_books_from_db()
        
        if not raw_data:
            print("WARNING: No book data returned from Firebase. Check your 'books' collection.")
            return False

        df = pd.DataFrame(raw_data) 
        print(f"Loaded {len(df)} records from Firebase.")

        # 2. Data Cleaning and Prep (Resilient against missing columns)
        required_cols = ['book_id', 'description', 'genres', 'title', 'image_url', 'author']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        
        # Drop rows where 'book_id' (the primary key) is missing
        df.dropna(subset=['book_id'], inplace=True)
        
        # Fill remaining NaNs for text columns with empty strings
        df['description'] = df['description'].fillna('')
        df['genres'] = df['genres'].fillna('')
        df['title'] = df['title'].fillna('Unknown Title')
        
        # Ensure book_id is the index
        df['book_id'] = df['book_id'].astype(str)
        df.set_index('book_id', inplace=True) 

        # 3. Feature Engineering
        df['soup'] = df['title'] + ' ' + df['description'] + ' ' + df['genres']
        
        # 4. Vectorization and Cosine Similarity
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['soup'])
        cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
        
        # 5. Save Model Components
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(base_dir, 'models')
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
            
        joblib.dump(cosine_sim, os.path.join(models_dir, 'similarity_matrix.joblib'))
        joblib.dump(df, os.path.join(models_dir, 'book_data_processed.joblib'))
        print("Model training complete. Files saved.")
        return True
        
    except Exception as e:
        print(f"FATAL ERROR during training: {e}")
        return False

if __name__ == "__main__":
    success = train_model()
    if not success:
        sys.exit(1)