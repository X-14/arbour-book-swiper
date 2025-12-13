// script.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";

// --- Firebase Config ---
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
let currentUser = null;

// --- Global DOM element selectors ---
const bookCard = document.getElementById("book-card");
const checkmark = document.getElementById("checkmark");
const xmark = document.getElementById("xmark");

// --- Element IDs matching the HTML structure ---
const titleEl = document.getElementById("title");
const descriptionEl = document.getElementById("description");
const imageEl = document.getElementById("image");
const scoreEl = document.getElementById("similiarityScore");
const authorEl = document.getElementById("author");
const likedByEl = document.getElementById("likedByContainer");

// --- Configuration for swipe animation ---
const moveDistance = 500; // Move further off-screen for a clear swipe
const animationDuration = 500; // 0.5 seconds

// --- State Management ---
let isSwiping = false; // Prevent rapid key presses from crashing the script
let touchStartX = 0;
let touchEndX = 0;

// --- Auth Listener ---
onAuthStateChanged(auth, (user) => {
    if (user) {
        currentUser = user;
        console.log("User authenticated:", user.uid);

        // Update nav link for Swipe (current page)
        const navSwipe = document.getElementById("navSwipe");
        if (navSwipe) navSwipe.href = `/recommendation?user_id=${user.uid}`;

    } else {
        console.log("User not authenticated. Redirecting to login...");
        window.location.href = "/"; // Redirect to login if not authenticated
    }
});

// Logout
const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
        const { signOut } = await import("https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js");
        await signOut(auth);
        window.location.href = "/";
    });
}

// --- FUNCTION: Send Swipe Data to Flask ---
async function sendSwipe(action) {
    const currentBookId = bookCard.dataset.bookId;

    if (currentBookId === 'DONE') {
        console.log("No more recommendations. Ignoring swipe.");
        return;
    }

    if (!currentUser) {
        alert("Please log in to swipe.");
        return;
    }

    try {
        const response = await fetch('/api/swipe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                book_id: currentBookId,
                action: action,
                user_id: currentUser.uid
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        updateBookCard(data);

    } catch (error) {
        console.error('Error during swipe API call:', error);
        alert('Could not connect to the server or Firebase.');
    } finally {
        isSwiping = false; // Allow the next swipe
        console.log("Swipe complete. isSwiping reset to false.");
    }
}


// --- FUNCTION: Update the card with the next book's details ---
function updateBookCard(data) {
    // 1. Check for "No more recommendations" fallback
    if (data.book_id === 'DONE') {
        titleEl.textContent = data.title;
        descriptionEl.textContent = data.description;
        scoreEl.textContent = "";
        imageEl.src = "";
        authorEl.textContent = "";
        if (likedByEl) likedByEl.textContent = "";
        bookCard.dataset.bookId = "DONE";
        return;
    }

    // 2. Update the card with the new book's details
    bookCard.dataset.bookId = data.book_id; // Set the next book ID
    titleEl.textContent = data.title;
    descriptionEl.textContent = data.description;
    authorEl.textContent = data.author || 'Unknown Author';

    if (likedByEl) {
        if (data.liked_by && data.liked_by.length > 0) {
            likedByEl.textContent = `Liked by: ${data.liked_by.join(', ')}`;
            likedByEl.style.display = 'block';
        } else {
            likedByEl.textContent = '';
            likedByEl.style.display = 'none';
        }
    }

    // Format and display the similarity score
    scoreEl.textContent = `Similarity: ${data.score ? data.score.toFixed(2) + '%' : 'N/A'}`;

    // Update the image source (direct Firebase URL)
    imageEl.src = data.image_url;
}


// --- Keydown Listener for Swiping (The Core Logic) ---
document.addEventListener("keydown", (event) => {
    // console.log("Key pressed:", event.key); // DEBUG LOG
    let action = '';
    let translateX = 0;

    if (isSwiping) return; // Prevent multiple swipes at once

    // 1. Determine Action
    if (event.key === "ArrowLeft") {
        action = 'dislike';
        translateX = -moveDistance; // Move left
    } else if (event.key === "ArrowRight") {
        action = 'like';
        translateX = moveDistance; // Move right
    } else {
        return; // Ignore other keys
    }

    event.preventDefault(); // Stop the browser from scrolling
    isSwiping = true;

    // 2. Visual Animation (Move the card)
    const indicator = (action === 'like' ? checkmark : xmark);

    // Show indicator and move card
    indicator.style.opacity = '1';
    indicator.style.width = '200px';
    indicator.style.height = '200px';
    bookCard.style.transform = `translateX(${translateX}px) rotate(${translateX / 30}deg)`;
    bookCard.style.opacity = '0'; // Fade out the card

    // 3. Send Data to Server (This runs concurrently with the animation)
    sendSwipe(action);

    // 4. CRITICAL: Reset the Card after the animation duration
    setTimeout(() => {
        // Reset indicators
        checkmark.style.opacity = '0';
        xmark.style.opacity = '0';
        checkmark.style.width = '0px';
        checkmark.style.height = '0px';
        xmark.style.width = '0px';
        xmark.style.height = '0px';

        // Reset card position and opacity instantly
        bookCard.style.transition = 'none';
        bookCard.style.transform = 'none';
        bookCard.style.opacity = '1';

        // Re-enable transition for the next swipe
        setTimeout(() => {
            bookCard.style.transition = 'transform 0.5s ease-out, opacity 0.5s ease-out';
        }, 50); // Small delay to apply 'none' before re-enabling transition
    }, animationDuration); // Wait for the animation to finish
});

// --- Touch Event Listeners for Mobile Swiping ---

document.addEventListener('touchstart', (e) => {
    if (isSwiping) return;
    touchStartX = e.changedTouches[0].screenX;
}, false);

document.addEventListener('touchmove', (e) => {
    if (isSwiping) return;
    // Optional: Add specialized logic to move the card visually with the finger
    // For now, simpler implementation: just detect the end of the swipe
}, false);

document.addEventListener('touchend', (e) => {
    if (isSwiping) return;
    touchEndX = e.changedTouches[0].screenX;
    handleTouchSwipe();
}, false);

function handleTouchSwipe() {
    const swipeThreshold = 50; // Minimum distance to be considered a swipe
    const swipeDistance = touchEndX - touchStartX;

    let action = '';
    let translateX = 0;

    if (Math.abs(swipeDistance) < swipeThreshold) return; // Not a swipe

    if (swipeDistance > 0) {
        // Swipe Right -> Like
        action = 'like';
        translateX = moveDistance;
    } else {
        // Swipe Left -> Dislike
        action = 'dislike';
        translateX = -moveDistance;
    }

    // Trigger visual feedback (Dry Principle: Reuse logic?)
    // To cleanly reuse the logic inside the keydown listener, we should ideally refactor.
    // However, I will duplicate the minimal animation logic here to ensure it works immediately 
    // without risking breaking the existing keydown flow during this prompt turn.

    isSwiping = true;
    const indicator = (action === 'like' ? checkmark : xmark);

    indicator.style.opacity = '1';
    indicator.style.width = '200px';
    indicator.style.height = '200px';

    // Animate card
    bookCard.style.transition = 'transform 0.5s ease-out, opacity 0.5s ease-out';
    bookCard.style.transform = `translateX(${translateX}px) rotate(${translateX / 30}deg)`;
    bookCard.style.opacity = '0';

    // Send Data
    sendSwipe(action);

    // Reset loop
    setTimeout(() => {
        checkmark.style.opacity = '0';
        xmark.style.opacity = '0';
        checkmark.style.width = '0px';
        checkmark.style.height = '0px';
        xmark.style.width = '0px';
        xmark.style.height = '0px';

        bookCard.style.transition = 'none';
        bookCard.style.transform = 'none';
        bookCard.style.opacity = '1';

        setTimeout(() => {
            bookCard.style.transition = 'transform 0.5s ease-out, opacity 0.5s ease-out';
        }, 50);
    }, animationDuration);
}