/**
 * Notification System for Hellio HR
 * Handles real-time notification display and interaction
 */

const NotificationManager = {
    apiUrl: 'http://localhost:8001/api/notifications',
    pollInterval: 10000, // Poll every 10 seconds
    pollTimer: null,

    init() {
        this.setupEventListeners();
        this.loadNotifications();
        this.startPolling();
    },

    setupEventListeners() {
        // Toggle notification panel
        document.getElementById('notification-bell').addEventListener('click', (e) => {
            e.stopPropagation();
            this.togglePanel();
        });

        // Mark all as read
        document.getElementById('mark-all-read-btn').addEventListener('click', () => {
            this.markAllAsRead();
        });

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            const panel = document.getElementById('notification-panel');
            const bell = document.getElementById('notification-bell');
            if (!panel.contains(e.target) && !bell.contains(e.target)) {
                this.closePanel();
            }
        });
    },

    togglePanel() {
        const panel = document.getElementById('notification-panel');
        panel.classList.toggle('show');
        if (panel.classList.contains('show')) {
            this.loadNotifications();
        }
    },

    closePanel() {
        const panel = document.getElementById('notification-panel');
        panel.classList.remove('show');
    },

    async loadNotifications() {
        try {
            const response = await fetch(this.apiUrl);
            const notifications = await response.json();
            console.log('LOADED NOTIFICATIONS:', notifications);
            console.log('First notification metadata:', notifications[0]?.metadata);
            this.renderNotifications(notifications);
            this.updateBadge(notifications);
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    },

    renderNotifications(notifications) {
        const container = document.getElementById('notification-list');

        if (notifications.length === 0) {
            container.innerHTML = `
                <div class="notification-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                    <p><strong>No notifications yet</strong></p>
                    <p>You're all caught up!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = notifications.map(notif => this.renderNotificationItem(notif)).join('');

        // Add click handlers for each notification
        container.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = parseInt(item.dataset.id);
                const actionUrl = item.dataset.actionUrl;
                this.handleNotificationClick(id, actionUrl);
            });
        });
    },

    renderNotificationItem(notif) {
        const isUnread = !notif.is_read;
        const timeAgo = this.getTimeAgo(notif.created_at);
        const icon = this.getNotificationIcon(notif.type);
        const actionButtons = this.renderActionButtons(notif.metadata?.action_buttons);

        return `
            <div class="notification-item ${isUnread ? 'unread' : ''}"
                 data-id="${notif.id}"
                 data-action-url="${notif.action_url || ''}">
                <div class="notification-item-wrapper">
                    <div class="notification-icon ${icon.class}">
                        ${icon.emoji}
                    </div>
                    <div class="notification-body">
                        <div class="notification-summary">${notif.summary}</div>
                        <div class="notification-time">${timeAgo}</div>
                        ${actionButtons}
                    </div>
                </div>
            </div>
        `;
    },

    renderActionButtons(actionButtons) {
        console.log('Action buttons:', actionButtons); // Debug
        if (!actionButtons || actionButtons.length === 0) {
            return '';
        }

        const buttonsHtml = actionButtons.map(action => {
            const buttonClass = action.primary ? 'notification-action-btn primary' : 'notification-action-btn';
            const confirmAttr = action.confirm ? `data-confirm="${action.confirm}"` : '';

            return `
                <button class="${buttonClass}"
                        data-url="${action.url}"
                        data-type="${action.type}"
                        ${confirmAttr}
                        onclick="NotificationManager.handleActionClick(event, '${action.url}', '${action.type}', ${action.confirm ? `'${action.confirm}'` : 'null'})">
                    <span class="btn-icon">${action.icon}</span>
                    <span class="btn-label">${action.label}</span>
                </button>
            `;
        }).join('');

        return `
            <div class="notification-actions" onclick="event.stopPropagation()">
                ${buttonsHtml}
            </div>
        `;
    },

    handleActionClick(event, url, type, confirmMessage) {
        event.stopPropagation();

        // Show confirmation if needed
        if (confirmMessage && !confirm(confirmMessage)) {
            return;
        }

        // Handle different action types
        switch (type) {
            case 'gmail_draft':
                // Open Gmail draft in new tab
                window.open(url, '_blank');
                break;

            case 'gmail_send':
                // Send draft via backend API
                this.sendDraft(url);
                break;

            case 'frontend_link':
                // Navigate within app
                if (url.includes('/candidates/')) {
                    const candidateId = url.split('/candidates/')[1];
                    if (window.viewCandidateProfile) {
                        this.closePanel();
                        window.viewCandidateProfile(candidateId);
                    }
                } else if (url.includes('/positions/')) {
                    const positionId = url.split('/positions/')[1];
                    this.closePanel();
                    // Switch to positions view
                    const positionsBtn = document.querySelector('[data-view="positions"]');
                    if (positionsBtn) {
                        positionsBtn.click();
                    }
                    // Wait a bit for the view to load, then show the position
                    setTimeout(() => {
                        if (window.showPositionDetail) {
                            window.showPositionDetail(positionId);
                        }
                    }, 100);
                }
                break;

            default:
                // Default: open in new tab
                window.open(url, '_blank');
        }
    },

    async sendDraft(sendUrl) {
        try {
            const response = await fetch(sendUrl, {
                method: 'POST',
            });

            if (response.ok) {
                alert('Email sent successfully!');
                this.loadNotifications();
            } else {
                alert('Failed to send email. Please try again.');
            }
        } catch (error) {
            console.error('Failed to send draft:', error);
            alert('Failed to send email. Please try again.');
        }
    },

    getNotificationIcon(type) {
        const icons = {
            'candidate_received': { emoji: '👤', class: 'candidate' },
            'position_created': { emoji: '📋', class: 'position' },
            'match_found': { emoji: '✨', class: 'candidate' },
            'alert': { emoji: '⚠️', class: 'alert' },
        };
        return icons[type] || { emoji: '📬', class: 'candidate' };
    },

    getTimeAgo(timestamp) {
        if (!timestamp) return 'Just now';

        const now = new Date();
        const time = new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return time.toLocaleDateString();
    },

    updateBadge(notifications) {
        const unreadCount = notifications.filter(n => !n.is_read).length;
        const badge = document.getElementById('notification-badge');

        if (unreadCount > 0) {
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    },

    async handleNotificationClick(id, actionUrl) {
        // Mark as read
        await this.markAsRead(id);

        // Navigate to action URL if provided
        if (actionUrl && actionUrl !== 'null') {
            // If it's a candidate URL, parse and navigate
            if (actionUrl.includes('/candidates/')) {
                const candidateId = actionUrl.split('/candidates/')[1];
                // Trigger view in app.js if available
                if (window.viewCandidateProfile) {
                    this.closePanel();
                    window.viewCandidateProfile(candidateId);
                }
            }
        }

        // Reload notifications to reflect read status
        this.loadNotifications();
    },

    async markAsRead(id) {
        try {
            await fetch(`${this.apiUrl}/${id}/read`, {
                method: 'PATCH',
            });
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    },

    async markAllAsRead() {
        try {
            await fetch(`${this.apiUrl}/read-all`, {
                method: 'PATCH',
            });
            this.loadNotifications();
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    },

    startPolling() {
        // Initial load
        this.loadNotifications();

        // Poll for new notifications every 10 seconds
        this.pollTimer = setInterval(() => {
            this.loadNotifications();
        }, this.pollInterval);
    },

    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }
};

// Initialize notification system when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => NotificationManager.init());
} else {
    NotificationManager.init();
}

// Expose for external access if needed
window.NotificationManager = NotificationManager;
