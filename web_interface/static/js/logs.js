/**
 * Logs JavaScript
 * Handles real-time log streaming and filtering
 */

class LogManager {
    constructor() {
        this.logs = [];
        this.maxLogs = 1000;
        this.filters = {
            level: 'all',
            search: ''
        };
        this.autoscroll = true;
        this.listeners = [];
    }

    addLog(log) {
        this.logs.push(log);

        // Keep only the last N logs
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }

        this.notifyListeners();
    }

    addLogs(logs) {
        this.logs.push(...logs);

        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }

        this.notifyListeners();
    }

    clearLogs() {
        this.logs = [];
        this.notifyListeners();
    }

    getFilteredLogs() {
        let filtered = this.logs;

        // Filter by level
        if (this.filters.level !== 'all') {
            filtered = filtered.filter(log => log.level === this.filters.level);
        }

        // Filter by search term
        if (this.filters.search) {
            const searchLower = this.filters.search.toLowerCase();
            filtered = filtered.filter(log =>
                log.message.toLowerCase().includes(searchLower)
            );
        }

        return filtered;
    }

    setFilter(type, value) {
        this.filters[type] = value;
        this.notifyListeners();
    }

    onChange(callback) {
        this.listeners.push(callback);
    }

    notifyListeners() {
        this.listeners.forEach(callback => callback(this.getFilteredLogs()));
    }

    exportLogs(format = 'json') {
        const logs = this.getFilteredLogs();

        if (format === 'json') {
            return JSON.stringify(logs, null, 2);
        } else if (format === 'txt') {
            return logs.map(log =>
                `[${new Date(log.timestamp).toISOString()}] [${log.level.toUpperCase()}] ${log.message}`
            ).join('\n');
        }

        return logs;
    }
}

class LogRenderer {
    constructor(container, logManager) {
        this.container = container;
        this.logManager = logManager;
        this.autoscroll = true;
    }

    render() {
        const logs = this.logManager.getFilteredLogs();
        this.container.innerHTML = '';

        if (logs.length === 0) {
            this.renderEmptyState();
            return;
        }

        logs.forEach((log, index) => {
            const logElement = this.createLogElement(log, index);
            this.container.appendChild(logElement);
        });

        if (this.autoscroll) {
            this.scrollToBottom();
        }
    }

    createLogElement(log, index) {
        const div = document.createElement('div');
        div.className = this.getLogClasses(log.level);

        const timestamp = this.formatTimestamp(log.timestamp);
        const levelDot = this.getLevelDotClass(log.level);

        div.innerHTML = `
            <span class="text-gray-500 flex-shrink-0">${timestamp}</span>
            <span class="${levelDot} h-1.5 w-1.5 rounded-full mt-1.5 flex-shrink-0"></span>
            <span class="flex-1 break-words">${this.escapeHtml(log.message)}</span>
        `;

        return div;
    }

    getLogClasses(level) {
        const baseClasses = 'flex items-start space-x-3 py-1 px-2 hover:bg-gray-800 rounded transition-colors';
        const colorClasses = {
            'info': 'text-blue-400',
            'success': 'text-green-400',
            'error': 'text-red-400',
            'default': 'text-gray-400'
        };

        return `${baseClasses} ${colorClasses[level] || colorClasses.default}`;
    }

    getLevelDotClass(level) {
        const colors = {
            'info': 'bg-blue-500',
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'default': 'bg-gray-500'
        };

        return colors[level] || colors.default;
    }

    renderEmptyState() {
        this.container.innerHTML = `
            <div class="flex items-center justify-center h-full text-gray-500">
                <div class="text-center">
                    <i data-lucide="terminal" class="h-12 w-12 mx-auto mb-2 opacity-50"></i>
                    <p>No logs to display</p>
                    <p class="text-xs mt-1">Logs will appear here as features run</p>
                </div>
            </div>
        `;
        lucide.createIcons();
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { hour12: false });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        this.container.scrollTop = this.container.scrollHeight;
    }

    setAutoscroll(enabled) {
        this.autoscroll = enabled;
    }
}

// Export utilities
const logUtils = {
    /**
     * Download logs as file
     */
    downloadLogs(logs, filename = 'osint-logs', format = 'json') {
        let content;
        let mimeType;

        if (format === 'json') {
            content = JSON.stringify(logs, null, 2);
            mimeType = 'application/json';
        } else if (format === 'txt') {
            content = logs.map(log =>
                `[${new Date(log.timestamp).toISOString()}] [${log.level.toUpperCase()}] ${log.message}`
            ).join('\n');
            mimeType = 'text/plain';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${filename}.${format}`;
        link.click();
        URL.revokeObjectURL(url);
    },

    /**
     * Parse log level from message
     */
    parseLogLevel(message) {
        if (message.includes('ERROR') || message.includes('✗')) return 'error';
        if (message.includes('SUCCESS') || message.includes('✓')) return 'success';
        return 'info';
    },

    /**
     * Highlight search term in log message
     */
    highlightSearchTerm(message, term) {
        if (!term) return message;

        const regex = new RegExp(`(${term})`, 'gi');
        return message.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LogManager,
        LogRenderer,
        logUtils
    };
}
