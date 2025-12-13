import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import { getAuth, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";

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

// AUTH STATE & LOAD
onAuthStateChanged(auth, async (user) => {
    if (user) {
        document.getElementById("navSwipe").href = `/recommendation?user_id=${user.uid}`;
        loadFriendsData(user.uid);
    } else {
        window.location.href = "/";
    }
});

document.getElementById("logoutBtn").addEventListener("click", () => {
    signOut(auth).then(() => window.location.href = "/");
});

// SEARCH USERS
document.getElementById("userSearchInput").placeholder = "Search by email address..."; // Added this line
document.getElementById("searchBtn").addEventListener("click", async () => {
    const query = document.getElementById("userSearchInput").value.trim();
    if (!query) return;

    // Check if it looks like an email
    if (!query.includes('@')) {
        alert("Please enter a valid email address.");
        return;
    }

    const resultsContainer = document.getElementById("searchResults");
    resultsContainer.innerHTML = "Searching...";

    try {
        const res = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`);
        const users = await res.json();

        if (users.length === 0) {
            resultsContainer.innerHTML = "No users found.";
            return;
        }

        const currentUser = auth.currentUser;

        resultsContainer.innerHTML = users.map(u => {
            if (currentUser && u.user_id === currentUser.uid) return ''; // Don't show self

            return `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #eee;">
                <span>${u.username}</span>
                <button onclick="window.sendRequest('${u.user_id}')" class="btn" style="width: auto; padding: 5px 10px; font-size: 0.8rem;">Add Friend</button>
            </div>
            `;
        }).join("");

    } catch (e) {
        console.error(e);
        resultsContainer.innerHTML = "Error searching users.";
    }
});

// SEND REQUEST
window.sendRequest = async (toUid) => {
    const user = auth.currentUser;
    if (!user) return;

    try {
        const res = await fetch('/api/friends/request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_uid: user.uid,
                to_uid: toUid
            })
        });

        const data = await res.json();
        if (res.ok) {
            alert("Request sent!");
        } else {
            alert(data.error || "Failed to send request.");
        }
    } catch (e) {
        alert("Error sending request.");
    }
};

// LOAD FRIENDS & REQUESTS
async function loadFriendsData(userId) {
    try {
        const res = await fetch(`/api/friends?user_id=${userId}`);
        const data = await res.json();

        // RENDER REQUESTS
        const reqList = document.getElementById("requestsList");
        const reqSection = document.getElementById("requestsSection");

        if (data.requests && data.requests.length > 0) {
            reqSection.style.display = 'block';
            reqList.innerHTML = data.requests.map(r => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: #fff8e1; margin-bottom: 5px; border-radius: 6px;">
                    <span><b>${r.sender_username}</b> wants to be friends.</span>
                    <div>
                        <button onclick="window.respondRequest('${r.id}', 'accepted')" class="btn" style="width: auto; background: #4caf50; padding: 5px 10px; margin-right: 5px;">Accept</button>
                        <button onclick="window.respondRequest('${r.id}', 'rejected')" class="btn" style="width: auto; background: #f44336; padding: 5px 10px;">Decline</button>
                    </div>
                </div>
            `).join("");
        } else {
            reqSection.style.display = 'none';
        }

        // RENDER FRIENDS
        const friendsList = document.getElementById("friendsList");
        if (data.friends && data.friends.length > 0) {
            friendsList.innerHTML = data.friends.map(f => `
                <div style="padding: 15px; border-bottom: 1px solid #eee;">
                    <span style="font-weight: 600; font-size: 1.1rem; display: block; margin-bottom: 5px;">${f.username}</span>
                    
                    ${f.top_books && f.top_books.length > 0 ? `
                        <div style="display: flex; gap: 10px; margin-top: 5px;">
                             ${f.top_books.map(b => `
                                <div style="width: 50px;" title="${b.title}">
                                    <img src="${b.image_url}" style="width: 100%; height: 75px; object-fit: cover; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                                </div>
                             `).join('')}
                        </div>
                        <p style="font-size: 0.8rem; color: #666; margin-top: 5px;">Recently liked books</p>
                    ` : '<p style="font-size: 0.8rem; color: #999;">No active preferences.</p>'}
                </div>
            `).join("");
        } else {
            friendsList.textContent = "No friends yet. Search for someone above!";
        }

    } catch (e) {
        console.error(e);
    }
}

// RESPOND TO REQUEST
window.respondRequest = async (reqId, status) => {
    try {
        const res = await fetch('/api/friends/respond', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: reqId, status: status })
        });

        if (res.ok) {
            // Reload
            const user = auth.currentUser;
            if (user) loadFriendsData(user.uid);
        } else {
            alert("Error responding.");
        }
    } catch (e) {
        console.error(e);
    }
};
