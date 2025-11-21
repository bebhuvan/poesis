// Load and display individual letter

async function loadLetter() {
    try {
        // Get letter ID from URL
        const params = new URLSearchParams(window.location.search);
        const letterId = parseInt(params.get('id'));

        if (!letterId) {
            showError('No letter ID specified');
            return;
        }

        // Load letters data
        const response = await fetch('letters.json');
        const data = await response.json();

        // Find the letter
        const letter = data.letters.find(l => l.number === letterId);

        if (!letter) {
            showError(`Letter ${letterId} not found`);
            return;
        }

        // Display the letter
        displayLetter(letter);

    } catch (error) {
        console.error('Error loading letter:', error);
        showError('Error loading letter');
    }
}

function displayLetter(letter) {
    const container = document.getElementById('letter-content');

    // Update page title
    const recipient = letter.recipient || 'Unknown Recipient';
    document.title = `Letter to ${recipient} - Dostoevsky Letters`;

    // Build HTML
    let html = `
        <div class="letter-header">
            <div class="letter-number">Letter ${letter.number}</div>
            <h1>To ${recipient}</h1>
            ${letter.date ? `<p class="letter-metadata"><strong>Date:</strong> ${letter.date}</p>` : ''}
            <p class="letter-metadata">
                <strong>Translator:</strong> Ethel Colburn Mayne<br>
                <strong>Source:</strong> <a href="${letter.source_url || '#'}" target="_blank">Letters of Fyodor Michailovitch Dostoevsky (1917)</a>
            </p>
        </div>

        <div class="letter-body">
            ${formatLetterBody(letter.body)}
        </div>
    `;

    // Add footnotes if present
    if (letter.footnotes && Object.keys(letter.footnotes).length > 0) {
        html += `
            <div class="footnotes">
                <h3>Footnotes</h3>
                ${formatFootnotes(letter.footnotes)}
            </div>
        `;
    }

    container.innerHTML = html;
}

function formatLetterBody(body) {
    if (!body) return '<p>No content available.</p>';

    // Split into paragraphs (double newline)
    const paragraphs = body.split(/\n\n+/);

    return paragraphs
        .filter(p => p.trim())
        .map(p => {
            // Clean up extra spaces
            const cleaned = p.trim().replace(/\s+/g, ' ');
            return `<p>${cleaned}</p>`;
        })
        .join('\n');
}

function formatFootnotes(footnotes) {
    return Object.entries(footnotes)
        .sort(([a], [b]) => {
            const numA = parseInt(a);
            const numB = parseInt(b);
            return numA - numB;
        })
        .map(([num, text]) => `
            <div class="footnote">
                <strong>[${num}]</strong> ${text}
            </div>
        `)
        .join('');
}

function showError(message) {
    const container = document.getElementById('letter-content');
    container.innerHTML = `
        <p class="loading">${message}</p>
        <p><a href="index.html">Return to letter list</a></p>
    `;
}

// Initialize
document.addEventListener('DOMContentLoaded', loadLetter);
