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

  document.getElementById("genreList").textContent =
    data.genres ? data.genres.join(", ") : "Not set";

  document.getElementById("freqInfo").textContent =
    data.frequency || "Not set";
});


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