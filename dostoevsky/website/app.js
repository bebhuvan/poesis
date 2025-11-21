// Load and display Dostoevsky letters

let allLetters = [];

// Load letters data
async function loadLetters() {
    try {
        const response = await fetch('letters.json');
        const data = await response.json();
        allLetters = data.letters;

        displayLetters(allLetters);
        setupSearch();
    } catch (error) {
        console.error('Error loading letters:', error);
        document.getElementById('letters-list').innerHTML =
            '<p class="loading">Error loading letters. Please ensure letters.json is in the same directory.</p>';
    }
}

// Display letters in grid
function displayLetters(letters) {
    const container = document.getElementById('letters-list');

    if (letters.length === 0) {
        container.innerHTML = '<p class="loading">No letters found.</p>';
        return;
    }

    container.innerHTML = '';

    letters.forEach(letter => {
        const card = createLetterCard(letter);
        container.appendChild(card);
    });

    // Add stats
    const stats = document.createElement('div');
    stats.className = 'stats';
    stats.innerHTML = `Showing ${letters.length} letter${letters.length !== 1 ? 's' : ''}`;
    container.before(stats);
}

// Create letter card element
function createLetterCard(letter) {
    const card = document.createElement('a');
    card.className = 'letter-card';
    card.href = `letter.html?id=${letter.number}`;

    const letterNumber = document.createElement('div');
    letterNumber.className = 'letter-number';
    letterNumber.textContent = `Letter ${letter.number}`;

    const title = document.createElement('h3');
    const recipient = letter.recipient || 'Unknown Recipient';
    title.textContent = `To ${recipient}`;

    const date = document.createElement('div');
    date.className = 'letter-date';
    date.textContent = letter.date || 'Date unknown';

    const preview = document.createElement('div');
    preview.className = 'letter-preview';
    const bodyText = letter.body || '';
    // Get first 150 characters
    const previewText = bodyText.substring(0, 150).trim() + (bodyText.length > 150 ? '...' : '');
    preview.textContent = previewText;

    card.appendChild(letterNumber);
    card.appendChild(title);
    card.appendChild(date);
    card.appendChild(preview);

    if (letter.footnotes && Object.keys(letter.footnotes).length > 0) {
        const footnotesBadge = document.createElement('span');
        footnotesBadge.className = 'has-footnotes';
        footnotesBadge.textContent = `${Object.keys(letter.footnotes).length} footnote${Object.keys(letter.footnotes).length > 1 ? 's' : ''}`;
        card.appendChild(footnotesBadge);
    }

    return card;
}

// Setup search functionality
function setupSearch() {
    // Add search box
    const searchHTML = `
        <div class="search-box">
            <input type="text" id="search-input" placeholder="Search letters by recipient, date, or content...">
        </div>
    `;

    const container = document.querySelector('.container');
    const gridSection = document.getElementById('letters-list');
    gridSection.insertAdjacentHTML('beforebegin', searchHTML);

    // Add event listener
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();

        if (!query) {
            displayLetters(allLetters);
            return;
        }

        const filtered = allLetters.filter(letter => {
            const recipient = (letter.recipient || '').toLowerCase();
            const date = (letter.date || '').toLowerCase();
            const body = (letter.body || '').toLowerCase();

            return recipient.includes(query) ||
                   date.includes(query) ||
                   body.includes(query);
        });

        displayLetters(filtered);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', loadLetters);
