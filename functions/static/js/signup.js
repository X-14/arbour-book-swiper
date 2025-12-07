// =========================
//  FIREBASE INITIALIZATION
// =========================
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import { 
  getAuth,
  GoogleAuthProvider, 
  signInWithPopup,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";

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

// =========================
//  FOOTER YEAR
// =========================
document.getElementById("year").textContent = new Date().getFullYear();

// =========================
//  GOOGLE SIGNUP
// =========================
document.getElementById("googleSignup").addEventListener("click", async () => {
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // First-time login → mark preferences as NOT done
    localStorage.setItem("preferencesDone", "false");

    // Redirect to preferences setup
    window.location.href = "preferences.html";

  } catch (err) {
    alert("Signup failed: " + err.message);
  }
});

// =========================
//  AUTO REDIRECT IF LOGGED IN
// =========================
onAuthStateChanged(auth, (user) => {
  if (user) {
    // If the user already logged in, send them forward
    const prefsDone = localStorage.getItem("preferencesDone");

    window.location.href = (prefsDone === "true")
      ? "homepage.html"
      : "preferences.html";
  }
});