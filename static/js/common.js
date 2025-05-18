/**
 * Common JavaScript functions for Product Evaluator
 */

// Global variables
const API_BASE_URL = '/api';

/**
 * API helper functions
 */
const API = {
  /**
   * Make a request to the API
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise} - Promise with response data
   */
  async request(endpoint, options = {}) {
    const token = localStorage.getItem('auth_token');
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      }
    };
    
    const fetchOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...(options.headers || {})
      }
    };
    
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);
      
      // Handle 401 Unauthorized responses
      if (response.status === 401) {
        // Clear auth data and redirect to login
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login';
        return null;
      }
      
      // For 204 No Content responses
      if (response.status === 204) {
        return { success: true };
      }
      
      // Try to parse JSON response
      const data = await response.json().catch(() => ({}));
      
      if (!response.ok) {
        throw new Error(data.detail || 'API request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  },
  
  /**
   * Make a GET request
   * @param {string} endpoint - API endpoint
   * @returns {Promise} - Promise with response data
   */
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },
  
  /**
   * Make a POST request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise} - Promise with response data
   */
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  /**
   * Make a PUT request
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise} - Promise with response data
   */
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },
  
  /**
   * Make a DELETE request
   * @param {string} endpoint - API endpoint
   * @returns {Promise} - Promise with response data
   */
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },
  
  /**
   * Make a form data POST request
   * @param {string} endpoint - API endpoint
   * @param {FormData} formData - Form data
   * @returns {Promise} - Promise with response data
   */
  async postForm(endpoint, formData) {
    const token = localStorage.getItem('auth_token');
    
    const options = {
      method: 'POST',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: formData
    };
    
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
      
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'API request failed');
      }
      
      return await response.json();
    } catch (error) {
      console.error('API form request error:', error);
      throw error;
    }
  }
};

/**
 * Authentication helpers
 */
const Auth = {
  /**
   * Check if user is authenticated
   * @returns {boolean} - True if authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('auth_token');
  },
  
  /**
   * Get current user information
   * @returns {Object|null} - User info or null
   */
  getUserInfo() {
    const userInfo = localStorage.getItem('user_info');
    return userInfo ? JSON.parse(userInfo) : null;
  },
  
  /**
   * Get username
   * @returns {string} - Username or 'User'
   */
  getUsername() {
    const userInfo = this.getUserInfo();
    return userInfo?.username || 'User';
  },
  
  /**
   * Require authentication (redirect to login if not authenticated)
   * @returns {boolean} - True if authenticated
   */
  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = '/login';
      return false;
    }
    return true;
  },
  
  /**
   * Redirect if authenticated
   * @param {string} destination - Destination URL
   * @returns {boolean} - True if redirected
   */
  redirectIfAuthenticated(destination = '/') {
    if (this.isAuthenticated()) {
      window.location.href = destination;
      return true;
    }
    return false;
  },
  
  /**
   * Logout user
   */
  logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
    window.location.href = '/login';
  }
};

/**
 * UI helpers
 */
const UI = {
  /**
   * Show toast notification
   * @param {string} message - Message to display
   * @param {string} type - Toast type (success, error, warning, info)
   * @param {number} duration - Duration in milliseconds
   */
  showToast(message, type = 'success', duration = 3000) {
    // Check if toast container exists, create if not
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'fixed bottom-4 right-4 z-50';
      document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `mb-3 p-3 rounded-lg shadow-lg ${
      type === 'success' ? 'bg-green-500' : 
      type === 'error' ? 'bg-red-500' : 
      type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
    } text-white`;
    
    toast.innerHTML = `
      <div class="flex items-center">
        <i class="mr-2 fas ${
          type === 'success' ? 'fa-check-circle' : 
          type === 'error' ? 'fa-exclamation-circle' : 
          type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'
        }"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.parentElement.remove()" class="ml-auto">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;
    
    // Add toast to container
    container.appendChild(toast);
    
    // Remove toast after duration
    setTimeout(() => {
      toast.classList.add('opacity-0', 'transition-opacity', 'duration-300');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },
  
  /**
   * Format date
   * @param {string} dateString - ISO date string
   * @param {Object} options - Date format options
   * @returns {string} - Formatted date
   */
  formatDate(dateString, options = {}) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const defaultOptions = {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    };
    
    return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
  },
  
  /**
   * Escape HTML
   * @param {string} text - Text to escape
   * @returns {string} - Escaped text
   */
  escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },
  
  /**
   * Format markdown (simple version)
   * @param {string} text - Markdown text
   * @returns {string} - HTML
   */
  formatMarkdown(text) {
    if (!text) return '';
    
    // Replace headers
    text = text.replace(/^#\s+(.+)$/gm, '<h3 class="font-semibold text-indigo-800 text-lg mt-4 mb-2">$1</h3>');
    text = text.replace(/^##\s+(.+)$/gm, '<h4 class="font-semibold text-indigo-700 mt-3 mb-1">$1</h4>');
    
    // Replace links
    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-indigo-600 hover:text-indigo-800" target="_blank">$1</a>');
    
    // Replace bold
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Replace italic
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Split into paragraphs
    const paragraphs = text.split(/\n\s*\n/);
    
    // Format paragraphs
    return paragraphs
      .map(p => {
        if (p.startsWith('<h')) return p;
        if (p.trim().length === 0) return '';
        return `<p class="mb-2">${p.trim()}</p>`;
      })
      .join('');
  },
  
  /**
   * Get score color class
   * @param {number} score - Score value
   * @returns {string} - CSS class
   */
  getScoreColor(score) {
    if (!score) return 'text-gray-500';
    if (score >= 8) return 'score-excellent';
    if (score >= 6) return 'score-good';
    if (score >= 4) return 'score-average';
    return 'score-poor';
  },
  
  /**
   * Get score background color class
   * @param {number} score - Score value
   * @returns {string} - CSS class
   */
  getScoreBgColor(score) {
    if (!score) return 'bg-gray-100';
    if (score >= 8) return 'score-bg-excellent';
    if (score >= 6) return 'score-bg-good';
    if (score >= 4) return 'score-bg-average';
    return 'score-bg-poor';
  }
};