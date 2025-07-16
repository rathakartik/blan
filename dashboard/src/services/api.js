import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setAuthToken(token) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken() {
    delete this.client.defaults.headers.common['Authorization'];
  }

  // Generic methods
  get(url, config = {}) {
    return this.client.get(url, config);
  }

  post(url, data = {}, config = {}) {
    return this.client.post(url, data, config);
  }

  put(url, data = {}, config = {}) {
    return this.client.put(url, data, config);
  }

  delete(url, config = {}) {
    return this.client.delete(url, config);
  }

  // Auth methods
  async login(email, password) {
    const response = await this.post('/api/auth/login', { email, password });
    return response.data;
  }

  async register(userData) {
    const response = await this.post('/api/auth/register', userData);
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.get('/api/auth/me');
    return response.data;
  }

  async forgotPassword(email) {
    const response = await this.post('/api/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(token, newPassword) {
    const response = await this.post('/api/auth/reset-password', { token, new_password: newPassword });
    return response.data;
  }

  // Sites methods
  async getSites() {
    const response = await this.get('/api/sites');
    return response.data;
  }

  async getSite(id) {
    const response = await this.get(`/api/sites/${id}`);
    return response.data;
  }

  async createSite(siteData) {
    const response = await this.post('/api/sites', siteData);
    return response.data;
  }

  async updateSite(id, siteData) {
    const response = await this.put(`/api/sites/${id}`, siteData);
    return response.data;
  }

  async deleteSite(id) {
    const response = await this.delete(`/api/sites/${id}`);
    return response.data;
  }

  // Analytics methods
  async getDashboardStats() {
    const response = await this.get('/api/analytics/dashboard');
    return response.data;
  }

  async getSiteAnalytics(siteId, days = 30) {
    const response = await this.get(`/api/analytics/sites/${siteId}?days=${days}`);
    return response.data;
  }

  // Widget methods
  async getEmbedScript(siteId) {
    const response = await this.get(`/api/sites/${siteId}/embed`);
    return response.data;
  }
}

export const api = new ApiService();
export default api;