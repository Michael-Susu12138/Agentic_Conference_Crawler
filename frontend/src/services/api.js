import axios from 'axios';

const API_URL = 'http://localhost:5000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions
export const ApiService = {
  // Status endpoint
  getApiStatus: async () => {
    try {
      const response = await apiClient.get('/api/status');
      return response.data;
    } catch (error) {
      console.error('Error fetching API status:', error);
      throw error;
    }
  },

  // Conferences endpoints
  getConferences: async (params = {}) => {
    try {
      let url = '/api/conferences';
      
      // Handle both string and object parameter formats
      if (typeof params === 'string') {
        // If it's just a research area string, convert to object
        url += `?area=${encodeURIComponent(params)}`;
      } else if (Object.keys(params).length > 0) {
        // Build query string from params object
        const queryParams = new URLSearchParams();
        if (params.area) queryParams.append('area', params.area);
        if (params.tier) queryParams.append('tier', params.tier);
        url += `?${queryParams.toString()}`;
      }
      
      const response = await apiClient.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching conferences:', error);
      throw error;
    }
  },

  refreshConferences: async (researchAreas) => {
    try {
      const response = await apiClient.post('/api/conferences/refresh', { research_areas: researchAreas });
      return response.data;
    } catch (error) {
      console.error('Error refreshing conferences:', error);
      throw error;
    }
  },

  // Papers endpoints
  getPapers: async (researchArea = null) => {
    try {
      const params = researchArea ? { area: researchArea } : {};
      const response = await apiClient.get('/api/papers', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching papers:', error);
      throw error;
    }
  },

  refreshPapers: async (researchAreas) => {
    try {
      const response = await apiClient.post('/api/papers/refresh', { research_areas: researchAreas });
      return response.data;
    } catch (error) {
      console.error('Error refreshing papers:', error);
      throw error;
    }
  },

  // Trends endpoint
  getTrends: async (researchArea = 'artificial intelligence', count = 10) => {
    try {
      const response = await apiClient.get(`/api/trends?area=${researchArea}&count=${count}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching trends:', error);
      throw error;
    }
  },

  // Query endpoint
  runQuery: async (query) => {
    try {
      const response = await apiClient.post('/api/query', { query });
      return response.data;
    } catch (error) {
      console.error('Error running query:', error);
      throw error;
    }
  },

  // Research Areas endpoints
  getResearchAreas: async () => {
    try {
      const response = await apiClient.get('/api/research-areas');
      return response.data;
    } catch (error) {
      console.error('Error fetching research areas:', error);
      throw error;
    }
  },

  updateResearchAreas: async (researchAreas) => {
    try {
      const response = await apiClient.post('/api/research-areas', { research_areas: researchAreas });
      return response.data;
    } catch (error) {
      console.error('Error updating research areas:', error);
      throw error;
    }
  }
};

export default ApiService; 