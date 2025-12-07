// =========================
//  FIREBASE SETUP
// =========================
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";
import {
  getFirestore,
  doc,
  getDoc,
  setDoc
} from "https://www.gstatic.com/firebasejs/10.13.1/firebase-firestore.js";

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


// =========================
//  AUTH CHECK
// =========================
let currentUser = null;

onAuthStateChanged(auth, async (user) => {
  if (!user) {
    window.location.href = "/";
    return;
  }

  currentUser = user;

  // Check Firestore: If preferencesDone = true → go straight home
  const userRef = doc(db, "users", currentUser.uid);
  const snap = await getDoc(userRef);

  if (snap.exists() && snap.data().preferencesDone === true) {
    window.location.href = `/recommendation?user_id=${currentUser.uid}`;
  }
});

// ... (skipping middle part) ...

// Redirect
window.location.href = "/home";


// =========================
//  LIMIT GENRES TO THREE
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const genreCheckboxes = document.querySelectorAll("input[name='genre']");

  genreCheckboxes.forEach(box => {
    box.addEventListener("change", () => {
      const selected = [...document.querySelectorAll("input[name='genre']:checked")];

      if (selected.length > 3) {
        box.checked = false;
        alert("You can only select EXACTLY 3 genres.");
      }
    });
  });
});


// =========================
//  FORM SUBMISSION
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("prefForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!currentUser) {
      alert("You must be logged in.");
      return;
    }

    // AGE (NEW)
    const age = document.getElementById("age").value;

    const genres = [...document.querySelectorAll("input[name='genre']:checked")].map(g => g.value);

    if (genres.length !== 3) {
      alert("Please select EXACTLY 3 genres.");
      return;
    }

    const frequency = document.querySelector("input[name='frequency']:checked")?.value;

    try {
      await setDoc(doc(db, "users", currentUser.uid), {
        age,
        genres,
        frequency,
        preferencesDone: true,
        updatedAt: new Date().toISOString()
      }, { merge: true });

      // Also store locally
      localStorage.setItem("preferencesDone", "true");

      // Redirect
      window.location.href = `/recommendation?user_id=${currentUser.uid}`;

    } catch (err) {
      alert("Error saving preferences: " + err.message);
    }
  });
});
