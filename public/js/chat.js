// Chat application logic
const API_BASE = 'http://localhost:8001';

// DOM elements
const chatModal = document.getElementById('chat-modal');
const openChatBtn = document.getElementById('open-chat-btn');
const closeChatBtn = document.getElementById('close-chat-btn');
const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const sendButton = document.getElementById('sendButton');
const exampleChips = document.getElementById('exampleChips');

// Modal control
if (openChatBtn) {
    openChatBtn.addEventListener('click', () => {
        chatModal.classList.add('active');
        questionInput.focus();
    });
}

if (closeChatBtn) {
    closeChatBtn.addEventListener('click', () => {
        chatModal.classList.remove('active');
    });
}

// Close modal when clicking outside
if (chatModal) {
    chatModal.addEventListener('click', (e) => {
        if (e.target === chatModal) {
            chatModal.classList.remove('active');
        }
    });
}

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && chatModal && chatModal.classList.contains('active')) {
        chatModal.classList.remove('active');
    }
});

// Load example questions on page load
async function loadExamples() {
    try {
        const response = await fetch(`${API_BASE}/api/chat/examples`);
        const data = await response.json();

        // Flatten all examples from all categories
        const allExamples = data.examples.flatMap(cat => cat.questions);

        // Display first 6 examples
        allExamples.slice(0, 6).forEach(question => {
            const chip = document.createElement('div');
            chip.className = 'example-chip';
            chip.textContent = question;
            chip.onclick = () => askQuestion(question);
            exampleChips.appendChild(chip);
        });
    } catch (error) {
        console.error('Failed to load examples:', error);
    }
}

// Add user message to chat
function addUserMessage(question) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="answer">${escapeHtml(question)}</div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Add assistant message to chat
function addAssistantMessage(response) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    // Show natural language answer
    let content = `<div class="answer">${escapeHtml(response.answer)}</div>`;

    // Add SQL trace if available (for transparency and debugging)
    if (response.sql) {
        const traceId = `trace-${Date.now()}`;
        content += `
            <div class="trace">
                <div class="trace-toggle" onclick="toggleTrace('${traceId}')">
                    📊 View SQL & Details
                </div>
                <div class="trace-details" id="${traceId}">
                    <div><strong>Rows returned:</strong> ${response.row_count}</div>
                    <div><strong>SQL Query:</strong></div>
                    <pre class="sql-code">${escapeHtml(response.sql)}</pre>
                </div>
            </div>
        `;
    }

    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Add error message to chat
function addErrorMessage(error) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="answer error">❌ Error: ${escapeHtml(error)}</div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Add loading indicator
function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant loading-message';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading"></div>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

// Remove loading indicator
function removeLoadingMessage(loadingDiv) {
    if (loadingDiv && loadingDiv.parentNode) {
        loadingDiv.parentNode.removeChild(loadingDiv);
    }
}

// Toggle trace visibility
function toggleTrace(traceId) {
    const traceDetails = document.getElementById(traceId);
    if (traceDetails) {
        traceDetails.classList.toggle('show');
    }
}

// Make toggleTrace available globally
window.toggleTrace = toggleTrace;

// Ask a question
async function askQuestion(question) {
    if (!question || !question.trim()) {
        return;
    }

    // Clear input if question came from input field
    if (question === questionInput.value) {
        questionInput.value = '';
    }

    // Add user message
    addUserMessage(question);

    // Show loading
    const loadingDiv = addLoadingMessage();

    // Disable input
    sendButton.disabled = true;
    questionInput.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/chat/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question.trim() }),
        });

        removeLoadingMessage(loadingDiv);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Request failed');
        }

        const data = await response.json();

        // Add assistant response
        addAssistantMessage(data);

    } catch (error) {
        removeLoadingMessage(loadingDiv);
        addErrorMessage(error.message);
        console.error('Error:', error);
    } finally {
        // Re-enable input
        sendButton.disabled = false;
        questionInput.disabled = false;
        questionInput.focus();
    }
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
if (sendButton) {
    sendButton.addEventListener('click', () => {
        askQuestion(questionInput.value);
    });
}

if (questionInput) {
    questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion(questionInput.value);
        }
    });
}

// Initialize
loadExamples();

// Only auto-focus on standalone page (not in modal)
if (!chatModal && questionInput) {
    questionInput.focus();
}
