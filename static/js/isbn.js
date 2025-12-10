// ==============================
// FIRESTORE SETUP

const db = firebase.firestore();


// Stores the ISBN of the book currently being processed in either section
let currentIsbn = null;

// DOM ELEMENTS for SECTION 1: ADD BOOK
const isbnInput = document.getElementById("isbnInput");
const searchBtn = document.getElementById("searchBtn");
const bookInfoDiv = document.getElementById("bookInfo");

// DOM ELEMENTS for SECTION 2: SEARCH DATABASE
const dbIsbnInput = document.getElementById("dbIsbnInput");
const dbSearchBtn = document.getElementById("dbSearchBtn");
const dbBookInfoDiv = document.getElementById("dbBookInfo");

const backToLoginBtn = document.getElementById("backToLoginBtn");

// ==============================
// INIT LOG (Confirms the new file is loaded)
// ==============================
console.log("isbn.js loaded - FINAL ATTEMPT WITH EVENT DELEGATION FIX.");

// ==============================
// BACK TO LOGIN
// ==============================
backToLoginBtn.addEventListener("click", () => {
    window.location.href = "/"; // Adjust to your actual login page
});

// ==============================
// FETCH FROM OPEN LIBRARY
// ==============================
async function fetchBookData(isbn) {
    try {
        const response = await fetch(`https://openlibrary.org/isbn/${isbn}.json`);
        if (!response.ok) return null;
        const data = await response.json();

        const cover = `https://covers.openlibrary.org/b/isbn/${isbn}-L.jpg`;

        let authors = [];
        if (data.authors) {
            for (let a of data.authors) {
                if (a.key) {
                    const aFetch = await fetch(`https://openlibrary.org${a.key}.json`);
                    const aData = await aFetch.json();
                    authors.push(aData.name);
                }
            }
        }

        let synopsis = data.description
            ? (typeof data.description === "string" ? data.description : data.description.value)
            : "N/A";

        let genres = data.subjects || [];
        genres = genres.map(g => g.replace(/\.$/, "").trim());
        if (!genres.length) genres = ["Unknown"];

        return {
            title: data.title || "N/A",
            author: authors.join(", ") || "Unknown",
            synopsis: synopsis,
            genre: genres,
            coverImage: cover
        };
    } catch (err) {
        console.error("Open Library Fetch error:", err);
        return null;
    }
}

// ==============================
// READ FORM FIELDS UTILITY - FINAL ROBUST PREFIX-BASED VERSION
// ==============================
function readFormFields(prefix = "") {
    const p = prefix ? prefix : "";

    const getElementValue = (id) => {
        const element = document.getElementById(id);
        if (element && 'value' in element) {
            return element.value.trim();
        } else {
            return "";
        }
    };

    const cover = getElementValue(`${p}CoverInput`);
    const title = getElementValue(`${p}TitleInput`);
    const authors = getElementValue(`${p}AuthorsInput`);
    const synopsis = getElementValue(`${p}SynopsisInput`);

    const genresValue = getElementValue(`${p}GenresInput`);
    const genres = genresValue
        .split(",")
        .map(g => g.trim())
        .filter(g => g.length);

    const finalBookData = {
        coverImage: cover || "N/A",
        title: title || "N/A",
        author: authors || "Unknown",
        synopsis: synopsis || "N/A",
        genre: genres.length ? genres : ["Unknown"]
    };

    console.log(`[READ ${prefix || 'ADD'}] Final Book Data:`, finalBookData);

    return finalBookData;
}

// ==============================
// DISPLAY ADD FORM (SECTION 1)
// ==============================
function displayAddForm(book) {
    bookInfoDiv.innerHTML = `
        <div class="book-display">
            <img src="${book.coverImage}" id="coverPreview">

            <div class="field">
                <span>Cover</span>
                <input id="coverInput" value="${book.coverImage}">
            </div>

            <div class="field">
                <span>Title</span>
                <input id="titleInput" value="${book.title}">
            </div>

            <div class="field">
                <span>Authors</span>
                <input id="authorsInput" value="${book.author}">
            </div>

            <div class="field">
                <span>Genres</span>
                <input id="genresInput" value="${book.genre.join(', ')}">
            </div>

            <div class="field">
                <span>Synopsis</span>
                <textarea id="synopsisInput">${book.synopsis}</textarea>
            </div>

            <button id="addBtn" 
                    class="btn btn--primary" 
                    data-isbn="${currentIsbn}">Add to Library</button>
        </div>
    `;

    // Live cover preview logic (This is correctly done after innerHTML)
    const coverInput = document.getElementById("coverInput");
    const coverPreview = document.getElementById("coverPreview");
    coverInput.addEventListener("input", () => {
        coverPreview.src = coverInput.value.trim();
    });

    // NOTE: The click listener for addBtn is now handled by the event listener on bookInfoDiv below!
}

// ==============================
// SAVE NEW BOOK (ADD BUTTON CLICK HANDLER) - REVERTED TO DIRECT ACCESS
// ==============================
function saveNewBook(event) {
    // Read the ISBN from the button (using event.target because of delegation)
    const isbnToSave = event.target.getAttribute("data-isbn");

    if (!isbnToSave) {
        console.error("Save failed: Could not retrieve ISBN from button data attribute.");
        alert("Error saving book: ISBN is missing.");
        return;
    }

    // 1. REVERTED: Read values directly using your proven method
    const titleValue = document.getElementById("titleInput").value.trim();
    const authorValue = document.getElementById("authorsInput").value.trim();
    const synopsisValue = document.getElementById("synopsisInput").value.trim();
    const coverValue = document.getElementById("coverInput").value.trim();

    // Process genres directly
    const genresElement = document.getElementById("genresInput");
    const genres = genresElement.value
        .split(",")
        .map(g => g.trim())
        .filter(g => g.length > 0);

    // 2. CRITICAL GUARD: Check if the fields are empty.
    if (!titleValue || !authorValue) {
        alert("Error reading form data. Please ensure the book details are populated.");
        console.error("Direct read failed: Title or Author input returned empty string.");
        return;
    }

    // 3. Assemble the book object using default fallbacks for null/empty data
    const book = {
        title: titleValue,
        author: authorValue,
        synopsis: synopsisValue || "N/A",
        coverImage: coverValue || "N/A",
        genre: genres.length ? genres : ["Unknown"]
    };

    console.log(`Attempting to add new book (${isbnToSave}) to Firestore...`, book);

    // 4. Write to Firestore
    db.collection("books")
        .doc(isbnToSave)
        .set(book, { merge: true })
        .then(() => {
            alert(`Book "${book.title}" added/updated successfully!`);
            console.log("Book saved successfully.");

            // Clean up the UI
            bookInfoDiv.innerHTML = "";
            isbnInput.value = "";
            currentIsbn = null;
        })
        .catch((err) => {
            console.error("Firestore write failed:", err);
            alert("Error saving book — check console for rules/network errors.");
        });
}

// ==============================
// EVENT DELEGATION LISTENER (FINAL FIX FOR SECTION 1)
// ==============================
// Attach ONE listener to the static parent container (bookInfoDiv)
// to handle clicks on the dynamically generated 'addBtn'.
bookInfoDiv.addEventListener("click", (e) => {
    // Check if the clicked element is the button we want (by ID)
    if (e.target.id === "addBtn") {
        saveNewBook(e); // Call the save function
    }
});


// ==============================
// SEARCH OPEN LIBRARY LISTENER (SECTION 1)
// ==============================
searchBtn.addEventListener("click", async () => {
    const isbn = isbnInput.value.trim().replace(/-/g, "");

    if (!isbn) return alert("Enter or scan ISBN to search Open Library");

    currentIsbn = isbn; // Set global ISBN to be passed to displayAddForm
    bookInfoDiv.innerHTML = "<p>Searching Open Library...</p>";

    const book = await fetchBookData(isbn);

    if (!book) {
        bookInfoDiv.innerHTML = "<p>Book not found in Open Library. You can try manually entering the details.</p>";
        // Optionally display an empty form for manual entry here
        return;
    }

    displayAddForm(book);
});

// ==============================
// SEARCH DATABASE LISTENER (SECTION 2)
// ==============================
dbSearchBtn.addEventListener("click", async () => {
    const isbn = dbIsbnInput.value.trim().replace(/-/g, "");
    if (!isbn) return alert("Enter or scan ISBN to look up");

    dbBookInfoDiv.innerHTML = "<p>Searching database...</p>";

    const doc = await db.collection("books").doc(isbn).get();

    if (!doc.exists) {
        dbBookInfoDiv.innerHTML = "<p>This book hasn't been added yet.</p>";
        return;
    }

    currentIsbn = isbn; // Set global ISBN for delete/update functions
    displayDbForm(doc.data());
});

// ==============================
// ENTER KEY SUPPORT
// ==============================
isbnInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") searchBtn.click();
});

dbIsbnInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") dbSearchBtn.click();
});

// ==============================
// DISPLAY DATABASE FORM
// ==============================
function displayDbForm(book) {
    // NOTE: Uses 'db' prefix for inputs
    dbBookInfoDiv.innerHTML = `
        <div class="book-display">
            <img src="${book.coverImage}" id="dbCoverPreview">

            <div class="field">
                <span>Cover</span>
                <input id="dbCoverInput" value="${book.coverImage}">
            </div>

            <div class="field">
                <span>Title</span>
                <input id="dbTitleInput" value="${book.title}">
            </div>

            <div class="field">
                <span>Authors</span>
                <input id="dbAuthorsInput" value="${book.author}">
            </div>

            <div class="field">
                <span>Genres</span>
                <input id="dbGenresInput" value="${book.genre.join(', ')}">
            </div>

            <div class="field">
                <span>Synopsis</span>
                <textarea id="dbSynopsisInput">${book.synopsis}</textarea>
            </div>

            <button id="updateBtn" class="btn btn--primary" data-isbn="${currentIsbn}">Save Changes</button>
            <button id="deleteBtn" class="btn btn--primary" style="background:red;color:white" data-isbn="${currentIsbn}">Delete Book</button>
        </div>
    `;

    // Attach listeners after injection
    document.getElementById("updateBtn").addEventListener("click", updateBook);
    document.getElementById("deleteBtn").addEventListener("click", deleteBook);

    // Live cover preview logic for DB form
    const dbCoverInput = document.getElementById("dbCoverInput");
    const dbCoverPreview = document.getElementById("dbCoverPreview");
    dbCoverInput.addEventListener("input", () => {
        dbCoverPreview.src = dbCoverInput.value.trim();
    });
}

// ==============================
// UPDATE BOOK
// ==============================
function updateBook(event) {
    // Read ISBN directly from the button
    const isbnToUpdate = event.currentTarget.getAttribute("data-isbn");

    if (!isbnToUpdate) return alert("Error: ISBN missing for update.");

    // Read fields using the 'db' prefix
    const updated = readFormFields("db");

    db.collection("books")
        .doc(isbnToUpdate)
        .update(updated)
        .then(() => {
            alert("Book updated successfully!");
            dbBookInfoDiv.innerHTML = "";
            dbIsbnInput.value = "";
            currentIsbn = null;
        })
        .catch((err) => {
            console.error("Update error:", err);
            alert("Error updating book");
        });
}

// ==============================
// DELETE BOOK
// ==============================
function deleteBook(event) {
    const isbnToDelete = event.currentTarget.getAttribute("data-isbn");

    if (!isbnToDelete) return alert("Error: ISBN missing for delete.");
    if (!confirm(`Are you sure you want to delete this book? (${isbnToDelete})`)) return;

    db.collection("books")
        .doc(isbnToDelete)
        .delete()
        .then(() => {
            alert("Book deleted successfully!");
            dbBookInfoDiv.innerHTML = "";
            dbIsbnInput.value = "";
            currentIsbn = null;
        })
        .catch((err) => {
            console.error("Delete error:", err);
            alert("Error deleting book");
        });
}