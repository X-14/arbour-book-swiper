/* =========================
    FIREBASE INITIALIZATION
   ========================= */
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
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
const provider = new GoogleAuthProvider();
const db = getFirestore(app);

// Make DB globally available for preferences.js
window.firebaseDB = db;

/* =========================
      FOOTER YEAR
   ========================= */
document.addEventListener("DOMContentLoaded", () => {
  const y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();

  /* =========================
        GOOGLE LOGIN
     ========================= */
  const googleBtn = document.getElementById("googleBtn");
  if (googleBtn) {
    googleBtn.addEventListener("click", async () => {
      try {
        const result = await signInWithPopup(auth, provider);
        const user = result.user;

        // Check Firestore user document
        const userRef = doc(db, "users", user.uid);
        const snap = await getDoc(userRef);

        if (!snap.exists()) {
          // First time user → create document
          await setDoc(userRef, {
            email: user.email,
            name: user.displayName,
            preferencesDone: false
          });

          window.location.href = "/preferences";
          return;
        }

        // Returning user — read preferences flag
        if (snap.data().preferencesDone === true) {
          window.location.href = `/recommendation?user_id=${user.uid}`;
        } else {
          window.location.href = "/preferences";
        }

      } catch (err) {
        alert("Google Sign-In failed: " + err.message);
      }
    });
  }

  /* =========================
        ADMIN LOGIN
     ========================= */
  const adminLoginBtn = document.getElementById("adminLoginBtn");
  if (adminLoginBtn) {
    adminLoginBtn.addEventListener("click", () => {
      const password = prompt("Enter admin password:");
      if (password === "12345") {
        window.location.href = "/isbn";
      } else {
        alert("Incorrect password. Access denied.");
      }
    });
  }

  /* =========================
     AUTO REDIRECT IF LOGGED IN
     ========================= */
  onAuthStateChanged(auth, async (user) => {
    // Check if we are on the login page (root or /login)
    const path = window.location.pathname;
    if (user && (path === "/" || path === "/login")) {
      const userRef = doc(db, "users", user.uid);
      const snap = await getDoc(userRef);

      if (!snap.exists()) {
        window.location.href = "/preferences";
        return;
      }

      if (snap.data().preferencesDone === true) {
        window.location.href = `/recommendation?user_id=${user.uid}`;
      } else {
        window.location.href = "/preferences";
      }
    }
  });
});
