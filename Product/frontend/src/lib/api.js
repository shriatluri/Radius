const API_BASE = '/v1';
const API_KEY_STORAGE = 'radius_api_key';

class ApiClient {
  constructor() {
    this.apiKey = localStorage.getItem(API_KEY_STORAGE) || null;
  }

  setApiKey(key) {
    this.apiKey = key;
    if (key) {
      localStorage.setItem(API_KEY_STORAGE, key);
    } else {
      localStorage.removeItem(API_KEY_STORAGE);
    }
  }

  getApiKey() {
    return this.apiKey;
  }

  clearApiKey() {
    this.setApiKey(null);
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response;
  }

  async listTransactions(filters = {}) {
    const params = new URLSearchParams();

    if (filters.status) params.append('status', filters.status);
    if (filters.business_id) params.append('business_id', filters.business_id);
    if (filters.risk_level) params.append('risk_level', filters.risk_level);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const queryString = params.toString();
    const endpoint = queryString ? `/transactions?${queryString}` : '/transactions';

    const response = await this.request(endpoint);
    return response.json();
  }

  async getAuditRecord(transactionId) {
    const response = await this.request(`/transactions/${transactionId}/audit`);
    return response.json();
  }

  async exportData(format = 'csv', filters = {}) {
    const params = new URLSearchParams({ format });

    if (filters.status) params.append('status', filters.status);
    if (filters.business_id) params.append('business_id', filters.business_id);
    if (filters.risk_level) params.append('risk_level', filters.risk_level);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);

    const endpoint = `/reports/export?${params.toString()}`;
    const response = await this.request(endpoint);

    if (format === 'csv') {
      // For CSV, return blob for download
      const blob = await response.blob();
      return blob;
    } else {
      // For JSON, return parsed data
      return response.json();
    }
  }

  async downloadCsv(filters = {}) {
    const blob = await this.exportData('csv', filters);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `radius_export_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
}

export const api = new ApiClient();
