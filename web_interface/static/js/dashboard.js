/**
 * Dashboard JavaScript
 * Handles real-time updates and interactions for the main dashboard
 */

// Utility functions
const utils = {
    /**
     * Format timestamp to relative time
     */
    formatRelativeTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;

        return date.toLocaleDateString();
    },

    /**
     * Format number with commas
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'success') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 max-w-sm w-full bg-white shadow-lg rounded-lg border pointer-events-auto toast ${type === 'error' ? 'border-red-200' : 'border-green-200'}`;
        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        ${type === 'success' ? '<i data-lucide="check-circle" class="h-6 w-6 text-green-500"></i>' : '<i data-lucide="alert-circle" class="h-6 w-6 text-red-500"></i>'}
                    </div>
                    <div class="ml-3 w-0 flex-1 pt-0.5">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                    </div>
                    <div class="ml-4 flex flex-shrink-0">
                        <button class="inline-flex rounded-md text-gray-400 hover:text-gray-500 focus:outline-none close-toast">
                            <i data-lucide="x" class="h-5 w-5"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(toast);
        lucide.createIcons();

        // Add close handler
        toast.querySelector('.close-toast').addEventListener('click', () => {
            toast.remove();
        });

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
};

// WebSocket connection manager
class SocketManager {
    constructor() {
        this.socket = null;
        this.listeners = {};
    }

    connect() {
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.emit('connection', { status: 'connected' });
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.emit('connection', { status: 'disconnected' });
        });

        this.socket.on('log_message', (log) => {
            this.emit('log', log);
        });

        this.socket.on('feature_update', (data) => {
            this.emit('feature_update', data);
        });

        this.socket.on('new_results', (data) => {
            this.emit('results', data);
        });
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }

    send(event, data) {
        if (this.socket) {
            this.socket.emit(event, data);
        }
    }
}

// API client
class APIClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async get(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }

    async post(endpoint, data) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    }
}

// Stats updater
class StatsUpdater {
    constructor(apiClient, updateInterval = 5000) {
        this.apiClient = apiClient;
        this.updateInterval = updateInterval;
        this.stats = {};
        this.listeners = [];
    }

    start() {
        this.update();
        setInterval(() => this.update(), this.updateInterval);
    }

    async update() {
        try {
            this.stats = await this.apiClient.get('/api/stats');
            this.notifyListeners();
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    onChange(callback) {
        this.listeners.push(callback);
    }

    notifyListeners() {
        this.listeners.forEach(callback => callback(this.stats));
    }
}

// Feature controller
class FeatureController {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.features = [];
    }

    async loadFeatures() {
        try {
            this.features = await this.apiClient.get('/api/features');
            return this.features;
        } catch (error) {
            console.error('Error loading features:', error);
            return [];
        }
    }

    async runFeature(featureId) {
        try {
            const result = await this.apiClient.post(`/api/features/${featureId}/run`, {});
            utils.showToast(`Feature "${result.feature.name}" started successfully`);
            return result;
        } catch (error) {
            console.error('Error running feature:', error);
            utils.showToast('Failed to start feature', 'error');
            throw error;
        }
    }

    getFeatureById(featureId) {
        return this.features.find(f => f.id === featureId);
    }

    getRunningFeatures() {
        return this.features.filter(f => f.status === 'running');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        utils,
        SocketManager,
        APIClient,
        StatsUpdater,
        FeatureController
    };
}
