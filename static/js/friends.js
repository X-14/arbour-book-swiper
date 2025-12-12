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
document.getElementById("searchBtn").addEventListener("click", async () => {
    const query = document.getElementById("userSearchInput").value.trim();
    if (!query) return;

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
                <div style="padding: 10px; border-bottom: 1px solid #eee;">
                    <span style="font-weight: 600;">${f.username}</span>
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
