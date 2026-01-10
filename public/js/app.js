// Application State
const state = {
    candidates: [],
    positions: [],
    selectedCandidates: new Set(),
    currentView: 'candidates',
    filters: {
        candidateSearch: '',
        candidateStatus: 'all',
        positionSearch: '',
        positionUrgency: 'all'
    }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    setupEventListeners();
    renderCandidates();
});

// Load Data from Backend API
async function loadData() {
    try {
        // Backend API base URL
        const API_BASE_URL = 'http://localhost:8001/api';

        // Load candidates from API
        const candidatesResponse = await fetch(`${API_BASE_URL}/candidates/`);
        state.candidates = await candidatesResponse.json();

        // Load positions from API
        const positionsResponse = await fetch(`${API_BASE_URL}/positions/`);
        state.positions = await positionsResponse.json();

        console.log('Data loaded successfully from backend:', state);
    } catch (error) {
        console.error('Error loading data from backend:', error);
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            // Only switch view if button has a data-view attribute
            if (view) {
                switchView(view);
            }
        });
    });

    // Candidate Search and Filters
    document.getElementById('candidate-search').addEventListener('input', (e) => {
        state.filters.candidateSearch = e.target.value;
        renderCandidates();
    });

    document.getElementById('candidate-status-filter').addEventListener('change', (e) => {
        state.filters.candidateStatus = e.target.value;
        renderCandidates();
    });

    // Position Search and Filters
    document.getElementById('position-search').addEventListener('input', (e) => {
        state.filters.positionSearch = e.target.value;
        renderPositions();
    });

    document.getElementById('position-urgency-filter').addEventListener('change', (e) => {
        state.filters.positionUrgency = e.target.value;
        renderPositions();
    });

    // Compare Button
    document.getElementById('compare-btn').addEventListener('click', showComparison);

    // Back Buttons
    document.getElementById('back-to-list-btn').addEventListener('click', () => {
        document.getElementById('candidate-profile').style.display = 'none';
        document.getElementById('candidate-list').style.display = 'grid';
        document.querySelector('.controls').style.display = 'flex';
    });

    document.getElementById('back-to-list-from-compare').addEventListener('click', () => {
        document.getElementById('comparison-view').style.display = 'none';
        document.getElementById('candidate-list').style.display = 'grid';
        document.querySelector('.controls').style.display = 'flex';
    });

    document.getElementById('back-to-positions-btn').addEventListener('click', () => {
        document.getElementById('position-detail').style.display = 'none';
        document.getElementById('position-list').style.display = 'grid';
        document.querySelectorAll('#positions-view .controls').forEach(el => el.style.display = 'flex');
    });
}

// View Switching
function switchView(view) {
    state.currentView = view;

    // Update nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Update views
    document.querySelectorAll('.view').forEach(v => {
        v.classList.toggle('active', v.id === `${view}-view`);
    });

    // Render appropriate content
    if (view === 'candidates') {
        renderCandidates();
    } else if (view === 'positions') {
        renderPositions();
    }
}

// Filter Candidates
function getFilteredCandidates() {
    let filtered = [...state.candidates];

    // Status filter
    if (state.filters.candidateStatus !== 'all') {
        filtered = filtered.filter(c => c.status === state.filters.candidateStatus);
    }

    // Search filter
    if (state.filters.candidateSearch) {
        const search = state.filters.candidateSearch.toLowerCase();
        filtered = filtered.filter(c => {
            const name = `${c.first_name} ${c.last_name}`.toLowerCase();
            const location = (c.location || '').toLowerCase();
            const skills = (c.skills || []).join(' ').toLowerCase();
            const summary = (c.summary || '').toLowerCase();
            return name.includes(search) || location.includes(search) ||
                   skills.includes(search) || summary.includes(search);
        });
    }

    return filtered;
}

// Render Candidates
function renderCandidates() {
    const container = document.getElementById('candidate-list');
    const filtered = getFilteredCandidates();

    if (filtered.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No candidates found</h3><p>Try adjusting your filters</p></div>';
        return;
    }

    container.innerHTML = filtered.map(candidate => `
        <div class="candidate-card" data-id="${candidate.id}">
            <div class="checkbox-wrapper">
                <input type="checkbox"
                       class="candidate-checkbox"
                       data-id="${candidate.id}"
                       ${state.selectedCandidates.has(candidate.id) ? 'checked' : ''}>
            </div>
            <div class="candidate-card-header">
                <div>
                    <h3>${candidate.first_name} ${candidate.last_name}</h3>
                    <p class="location">📍 ${candidate.location || 'Not specified'}</p>
                </div>
                <span class="status-badge ${candidate.status.toLowerCase()}">${candidate.status}</span>
            </div>
            <p class="summary">${candidate.summary || ''}</p>
            <div class="skills-preview">
                ${(candidate.skills || []).slice(0, 5).map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                ${(candidate.skills || []).length > 5 ? `<span class="skill-tag">+${(candidate.skills || []).length - 5} more</span>` : ''}
            </div>
            <p class="experience">
                ${(candidate.experience || []).length > 0 ?
                  `Currently: ${candidate.experience[0].title} at ${candidate.experience[0].company}` :
                  'No experience listed'}
            </p>
        </div>
    `).join('');

    // Add click listeners to cards
    container.querySelectorAll('.candidate-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.classList.contains('candidate-checkbox')) {
                return; // Don't show profile if clicking checkbox
            }
            showCandidateProfile(card.dataset.id);
        });
    });

    // Add checkbox listeners
    container.querySelectorAll('.candidate-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            toggleCandidateSelection(checkbox.dataset.id);
        });
    });

    updateCompareButton();
}

// Toggle Candidate Selection
function toggleCandidateSelection(candidateId) {
    if (state.selectedCandidates.has(candidateId)) {
        state.selectedCandidates.delete(candidateId);
    } else {
        state.selectedCandidates.add(candidateId);
    }

    // Update card styling
    document.querySelectorAll('.candidate-card').forEach(card => {
        if (card.dataset.id === candidateId) {
            card.classList.toggle('selected', state.selectedCandidates.has(candidateId));
        }
    });

    updateCompareButton();
}

// Update Compare Button
function updateCompareButton() {
    const compareBtn = document.getElementById('compare-btn');
    const count = state.selectedCandidates.size;

    if (count === 0) {
        // Hide button when nothing selected
        compareBtn.style.display = 'none';
    } else if (count === 1) {
        // Show disabled button with "min 2" message when 1 selected
        compareBtn.style.display = 'block';
        compareBtn.disabled = true;
        compareBtn.textContent = 'Compare Selected (min 2)';
    } else {
        // Enable button when 2+ selected
        compareBtn.style.display = 'block';
        compareBtn.disabled = false;
        compareBtn.textContent = `Compare ${count} Selected`;
    }
}

// Show Candidate Profile
function showCandidateProfile(candidateId) {
    const candidate = state.candidates.find(c => c.id === candidateId);
    if (!candidate) return;

    const container = document.getElementById('profile-content');
    container.innerHTML = `
        <div class="profile-header">
            <h2>${candidate.first_name} ${candidate.last_name}</h2>
            <div class="profile-meta">
                <div class="profile-meta-item">📧 ${candidate.email || 'Not specified'}</div>
                <div class="profile-meta-item">📱 ${candidate.phone || 'Not specified'}</div>
                <div class="profile-meta-item">📍 ${candidate.location || 'Not specified'}</div>
                ${candidate.linkedin ? `<div class="profile-meta-item">💼 <a href="https://${candidate.linkedin}" target="_blank">LinkedIn</a></div>` : ''}
                ${candidate.github ? `<div class="profile-meta-item">💻 <a href="https://${candidate.github}" target="_blank">GitHub</a></div>` : ''}
            </div>
        </div>

        <div class="profile-section">
            <h3>Summary</h3>
            <p>${candidate.summary || 'No summary provided'}</p>
        </div>

        <div class="profile-section">
            <h3>Skills</h3>
            <div class="skills-list">
                ${(candidate.skills || []).map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
            </div>
        </div>

        <div class="profile-section">
            <h3>Experience</h3>
            ${(candidate.experience || []).map(exp => `
                <div class="experience-item">
                    <h4>${exp.title}</h4>
                    <div class="company">${exp.company} - ${exp.location || 'Location not specified'}</div>
                    <div class="dates">${exp.start_date || 'N/A'} - ${exp.end_date || 'N/A'}</div>
                    <ul>
                        ${(exp.responsibilities || []).map(resp => `<li>${resp}</li>`).join('')}
                    </ul>
                </div>
            `).join('')}
        </div>

        <div class="profile-section">
            <h3>Education</h3>
            ${(candidate.education || []).map(edu => `
                <div class="education-item">
                    <h4>${edu.degree}</h4>
                    <div class="institution">${edu.institution}</div>
                    <div class="dates">${edu.start_date || 'N/A'} - ${edu.end_date || 'N/A'} (${edu.status || 'N/A'})</div>
                </div>
            `).join('')}
        </div>

        ${(candidate.certifications || []).length > 0 ? `
            <div class="profile-section">
                <h3>Certifications</h3>
                <div class="certifications-list">
                    ${candidate.certifications.map(cert => `
                        <div class="certification-item">
                            <div>
                                <div class="name">${cert.name}</div>
                                <div class="issuer">${cert.issuer}</div>
                            </div>
                            <div class="year">${cert.year || 'N/A'}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}

        <div class="profile-section">
            <h3>Languages</h3>
            <div class="languages-list">
                ${(candidate.languages || []).map(lang => `
                    <div class="language-item">
                        <div class="language">${lang.language}</div>
                        <div class="proficiency">${lang.proficiency}</div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="profile-section">
            <a href="${candidate.cvFile || '#'}" class="cv-link" target="_blank">📄 View Original CV</a>
        </div>
    `;

    document.getElementById('candidate-list').style.display = 'none';
    document.querySelector('.controls').style.display = 'none';
    document.getElementById('candidate-profile').style.display = 'block';
}

// Show Comparison
function showComparison() {
    if (state.selectedCandidates.size < 2) return;

    const selectedIds = Array.from(state.selectedCandidates);
    const candidates = selectedIds.map(id => state.candidates.find(c => c.id === id));

    const container = document.getElementById('comparison-content');
    container.innerHTML = candidates.map(candidate => `
        <div class="comparison-card">
            <div class="profile-header">
                <h3>${candidate.first_name} ${candidate.last_name}</h3>
                <div class="profile-meta">
                    <div class="profile-meta-item">📧 ${candidate.email || 'Not specified'}</div>
                    <div class="profile-meta-item">📍 ${candidate.location || 'Not specified'}</div>
                </div>
            </div>

            <div class="profile-section">
                <h4>Summary</h4>
                <p>${candidate.summary || 'No summary provided'}</p>
            </div>

            <div class="profile-section">
                <h4>Skills (${(candidate.skills || []).length})</h4>
                <div class="skills-list">
                    ${(candidate.skills || []).map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                </div>
            </div>

            <div class="profile-section">
                <h4>Experience</h4>
                ${(candidate.experience || []).slice(0, 2).map(exp => `
                    <div class="experience-item">
                        <h5>${exp.title}</h5>
                        <div class="company">${exp.company}</div>
                        <div class="dates">${exp.start_date || 'N/A'} - ${exp.end_date || 'N/A'}</div>
                    </div>
                `).join('')}
            </div>

            <div class="profile-section">
                <h4>Education</h4>
                ${(candidate.education || []).map(edu => `
                    <div>${edu.degree} - ${edu.institution}</div>
                `).join('')}
            </div>

            ${(candidate.certifications || []).length > 0 ? `
                <div class="profile-section">
                    <h4>Certifications (${candidate.certifications.length})</h4>
                    ${candidate.certifications.map(cert => `<div>• ${cert.name} (${cert.year || 'N/A'})</div>`).join('')}
                </div>
            ` : ''}

            <div class="profile-section">
                <a href="${candidate.cvFile || '#'}" class="cv-link" target="_blank">📄 View CV</a>
            </div>
        </div>
    `).join('');

    document.getElementById('candidate-list').style.display = 'none';
    document.querySelector('.controls').style.display = 'none';
    document.getElementById('comparison-view').style.display = 'block';
}

// Filter Positions
function getFilteredPositions() {
    let filtered = [...state.positions];

    // Urgency filter
    if (state.filters.positionUrgency !== 'all') {
        filtered = filtered.filter(p => p.urgency === state.filters.positionUrgency);
    }

    // Search filter
    if (state.filters.positionSearch) {
        const search = state.filters.positionSearch.toLowerCase();
        filtered = filtered.filter(p => {
            const title = p.title.toLowerCase();
            const company = p.company.toLowerCase();
            const description = p.description.toLowerCase();
            const skills = (p.skills || []).join(' ').toLowerCase();
            return title.includes(search) || company.includes(search) ||
                   description.includes(search) || skills.includes(search);
        });
    }

    return filtered;
}

// Render Positions
function renderPositions() {
    const container = document.getElementById('position-list');
    const filtered = getFilteredPositions();

    if (filtered.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No positions found</h3><p>Try adjusting your filters</p></div>';
        return;
    }

    container.innerHTML = filtered.map(position => `
        <div class="position-card" data-id="${position.id}">
            <div class="position-card-header">
                <div>
                    <h3>${position.title}</h3>
                    <p class="company">${position.company}</p>
                </div>
                <span class="urgency-badge ${position.urgency.toLowerCase()}">${position.urgency}</span>
            </div>
            <p class="description">${position.description}</p>
            <div class="skills-preview">
                ${(position.skills || []).slice(0, 5).map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                ${(position.skills || []).length > 5 ? `<span class="skill-tag">+${(position.skills || []).length - 5} more</span>` : ''}
            </div>
            <div class="meta">
                <div class="meta-item">📍 ${position.location}</div>
                <div class="meta-item">💼 ${position.experience}</div>
                <div class="meta-item">⏰ ${position.timeline}</div>
            </div>
        </div>
    `).join('');

    // Add click listeners
    container.querySelectorAll('.position-card').forEach(card => {
        card.addEventListener('click', () => {
            showPositionDetail(card.dataset.id);
        });
    });
}

// Show Position Detail
function showPositionDetail(positionId) {
    const position = state.positions.find(p => p.id === positionId);
    if (!position) return;

    const container = document.getElementById('position-content');
    container.innerHTML = `
        <div class="profile-header">
            <h2>${position.title}</h2>
            <div class="profile-meta">
                <div class="profile-meta-item">🏢 ${position.company}</div>
                <div class="profile-meta-item">📍 ${position.location}</div>
                <div class="profile-meta-item">💼 ${position.experience}</div>
                <div class="profile-meta-item">
                    <span class="urgency-badge ${position.urgency.toLowerCase()}">${position.urgency} Priority</span>
                </div>
            </div>
        </div>

        <div class="profile-section">
            <h3>Description</h3>
            <p>${position.description}</p>
        </div>

        <div class="profile-section">
            <h3>Requirements</h3>
            <ul class="requirements-list">
                ${position.requirements.map(req => `<li>${req}</li>`).join('')}
            </ul>
        </div>

        ${position.nice_to_have && position.nice_to_have.length > 0 ? `
            <div class="profile-section">
                <h3>Nice to Have</h3>
                <ul class="requirements-list">
                    ${position.nice_to_have.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        ` : ''}

        <div class="profile-section">
            <h3>Responsibilities</h3>
            <ul class="responsibilities-list">
                ${position.responsibilities.map(resp => `<li>${resp}</li>`).join('')}
            </ul>
        </div>

        ${(position.skills || []).length > 0 ? `
        <div class="profile-section">
            <h3>Required Skills</h3>
            <div class="skills-list">
                ${position.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
            </div>
        </div>
        ` : ''}

        <div class="profile-section">
            <h3>Position Details</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Work Arrangement</label>
                    <div class="value">${position.work_arrangement || 'Not specified'}</div>
                </div>
                <div class="info-item">
                    <label>Compensation</label>
                    <div class="value">${position.compensation}</div>
                </div>
                <div class="info-item">
                    <label>Hiring Timeline</label>
                    <div class="value">${position.timeline}</div>
                </div>
                <div class="info-item">
                    <label>Status</label>
                    <div class="value">${position.status}</div>
                </div>
            </div>
        </div>

        ${position.contact_person && (position.contact_person.name || position.contact_person.title || position.contact_person.email) ? `
        <div class="profile-section">
            <h3>Contact Person</h3>
            <div class="info-grid">
                <div class="info-item">
                    <label>Name</label>
                    <div class="value">${position.contact_person.name || 'Not specified'}</div>
                </div>
                <div class="info-item">
                    <label>Title</label>
                    <div class="value">${position.contact_person.title || 'Not specified'}</div>
                </div>
                <div class="info-item">
                    <label>Email</label>
                    <div class="value">${position.contact_person.email || 'Not specified'}</div>
                </div>
            </div>
        </div>
        ` : ''}

        ${position.notes ? `
            <div class="profile-section">
                <h3>Notes</h3>
                <p>${position.notes}</p>
            </div>
        ` : ''}

        <div class="profile-actions">
            <button id="edit-position-btn" class="primary-btn">Edit Position</button>
        </div>
    `;

    document.getElementById('position-list').style.display = 'none';
    document.querySelectorAll('#positions-view .controls').forEach(el => el.style.display = 'none');
    document.getElementById('position-detail').style.display = 'block';

    // Add edit button click handler
    document.getElementById('edit-position-btn').addEventListener('click', () => showPositionEditForm(positionId));
}

// Show position edit form
function showPositionEditForm(positionId) {
    const position = state.positions.find(p => p.id === positionId);
    if (!position) return;

    const container = document.getElementById('position-content');
    container.innerHTML = `
        <h2>Edit Position</h2>
        <form id="edit-position-form" class="edit-form">
            <div class="form-group">
                <label>Status</label>
                <select name="status" required>
                    <option value="Open" ${position.status === 'Open' ? 'selected' : ''}>Open</option>
                    <option value="Closed" ${position.status === 'Closed' ? 'selected' : ''}>Closed</option>
                    <option value="On Hold" ${position.status === 'On Hold' ? 'selected' : ''}>On Hold</option>
                </select>
            </div>

            <div class="form-group">
                <label>Urgency</label>
                <select name="urgency" required>
                    <option value="Critical" ${position.urgency === 'Critical' ? 'selected' : ''}>Critical</option>
                    <option value="High" ${position.urgency === 'High' ? 'selected' : ''}>High</option>
                    <option value="Medium" ${position.urgency === 'Medium' ? 'selected' : ''}>Medium</option>
                    <option value="Low" ${position.urgency === 'Low' ? 'selected' : ''}>Low</option>
                </select>
            </div>

            <div class="form-group">
                <label>Description</label>
                <textarea name="description" rows="4" required>${position.description}</textarea>
            </div>

            <div class="form-group">
                <label>Compensation</label>
                <input type="text" name="compensation" value="${position.compensation || ''}" />
            </div>

            <div class="form-group">
                <label>Timeline</label>
                <input type="text" name="timeline" value="${position.timeline || ''}" />
            </div>

            <div class="form-group">
                <label>Notes</label>
                <textarea name="notes" rows="3">${position.notes || ''}</textarea>
            </div>

            <div class="form-actions">
                <button type="submit" class="primary-btn">Save Changes</button>
                <button type="button" id="cancel-edit-btn" class="secondary-btn">Cancel</button>
            </div>
        </form>
    `;

    // Handle form submission
    document.getElementById('edit-position-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await savePositionChanges(positionId, new FormData(e.target));
    });

    // Handle cancel
    document.getElementById('cancel-edit-btn').addEventListener('click', () => showPositionDetail(positionId));
}

// Save position changes to backend
async function savePositionChanges(positionId, formData) {
    try {
        const API_BASE_URL = 'http://localhost:8001/api';
        const updateData = {
            status: formData.get('status'),
            urgency: formData.get('urgency'),
            description: formData.get('description'),
            compensation: formData.get('compensation'),
            timeline: formData.get('timeline'),
            notes: formData.get('notes')
        };

        const response = await fetch(`${API_BASE_URL}/positions/${positionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });

        if (!response.ok) {
            throw new Error('Failed to update position');
        }

        const updatedPosition = await response.json();

        // Update local state
        const index = state.positions.findIndex(p => p.id === positionId);
        if (index !== -1) {
            state.positions[index] = updatedPosition;
        }

        // Show success message
        alert('Position updated successfully!');

        // Return to position detail view
        showPositionDetail(positionId);
    } catch (error) {
        console.error('Error updating position:', error);
        alert('Failed to update position. Please try again.');
    }
}
