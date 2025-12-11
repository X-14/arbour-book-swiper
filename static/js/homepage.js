// ==========================
//   FIREBASE IMPORTS
// ==========================
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";

import {
  getFirestore,
  doc,
  getDoc
} from "https://www.gstatic.com/firebasejs/10.13.1/firebase-firestore.js";

// ==========================
//   FIREBASE CONFIG
// ==========================
const firebaseConfig = {
  apiKey: "AIzaSyDTUuPffjD2WeQC7MDlFKBCOcRAmREjWJs",
  authDomain: "booktinder-fb868.firebaseapp.com",
  projectId: "booktinder-fb868",
  storageBucket: "booktinder-fb868.firebasestorage.app",
  messagingSenderId: "660028415634",
  appId: "1:660028415634:web:c078752bb53502afcc904b",
  measurementId: "G-1WB2RYS3XB"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);


// ==========================
//   AUTH CHECK + LOAD DATA
// ==========================
onAuthStateChanged(auth, async (user) => {
  if (!user) {
    // If not logged in, redirect to the login page (index.html)
    window.location.href = "index.html";
    return;
  }

  document.getElementById("userInfo").textContent =
    `Logged in as: ${user.displayName || user.email}`;

  // Load Firestore user data
  const userDoc = await getDoc(doc(db, "users", user.uid));

  if (!userDoc.exists()) {
    document.getElementById("genreList").textContent = "No preferences found.";
    document.getElementById("freqInfo").textContent = "Unknown.";
    return;
  }

  const data = userDoc.data();

  data.genres ? data.genres.join(", ") : "Not set";

  document.getElementById("freqInfo").textContent =
    data.frequency || "Not set";

  // LOAD EXPLORE SECTION
  loadExploreBooks(user.uid);

  // Update nav link for Swipe (current page)
  const navSwipe = document.getElementById("navSwipe");
  if (navSwipe) navSwipe.href = `/recommendation?user_id=${user.uid}`;
});

async function loadExploreBooks(userId) {
  try {
    const res = await fetch(`/api/explore?user_id=${userId}`);
    const books = await res.json();

    const container = document.getElementById("exploreContainer");
    const list = document.getElementById("exploreList");

    if (books.length > 0) {
      container.style.display = 'block';
      list.innerHTML = books.map(book => `
                <div style="display: flex; align-items: start; gap: 15px; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 20px; position: relative;">
                    <img src="${book.image_url}" style="width: 80px; height: 120px; object-fit: cover; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="flex: 1;">
                        <h4 style="margin: 0; font-size: 1.1rem;">${book.title}</h4>
                        <p style="margin: 2px 0; font-size: 0.9rem; color: #555;">${book.author}</p>
                        
                        <p style="color: #4CAF50; font-weight: 600; font-size: 0.85rem; margin: 4px 0;">
                            ${book.score}
                        </p>
                        
                        <p style="margin: 8px 0; font-size: 0.85rem; color: #666; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                            ${book.description}
                        </p>

                        <button 
                            id="btn-${book.book_id}"
                            onclick="window.handleExploreLike('${book.book_id}')"
                            class="btn" 
                            style="margin-top: 5px; padding: 6px 12px; font-size: 0.85rem; width: auto; background-color: #2196F3;">
                            Like Book
                        </button>
                    </div>
                </div>
            `).join('');
    }
  } catch (e) {
    console.error("Error loading explore books:", e);
  }
}

// Global Like Function for Explore Section
window.handleExploreLike = async (bookId) => {
  const user = auth.currentUser;
  if (!user) return;

  try {
    const btn = document.getElementById(`btn-${bookId}`);
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Liking...";
      btn.style.opacity = "0.7";
    }

    const response = await fetch('/api/swipe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        book_id: bookId,
        action: 'like',
        user_id: user.uid
      })
    });

    if (response.ok) {
      if (btn) {
        btn.textContent = "Liked!";
        btn.style.backgroundColor = "#4CAF50";
        btn.style.color = "white";
        btn.style.border = "none";
        btn.removeAttribute("onclick");
      }
    } else {
      if (btn) {
        btn.textContent = "Error";
        btn.style.backgroundColor = "#d9534f";
        setTimeout(() => {
          btn.disabled = false;
          btn.textContent = "Like Book";
          btn.style.backgroundColor = "#2196F3";
        }, 2000);
      }
    }
  } catch (err) {
    console.error("Error liking book in explore:", err);
  }
};


// ==========================
//   LOGOUT BUTTON
// ==========================
document.getElementById("logoutBtn").addEventListener("click", async () => {
  await signOut(auth);
  window.location.href = "/";
});


// ==========================
//   RECOMMENDATIONS BUTTON
// ==========================
document.getElementById("goToRecs").addEventListener("click", () => {
  const user = auth.currentUser;
  if (user) {
    window.location.href = `/recommendation?user_id=${user.uid}`;
  } else {
    window.location.href = "/";
  }
});

// ==========================
//   EDIT PREFERENCES BUTTON
// ==========================
document.getElementById("editPrefsBtn").addEventListener("click", () => {
  window.location.href = "/preferences";
});