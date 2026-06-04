import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const res = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refresh });
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  updateProfile: (data) => api.patch('/auth/me', data),
};

export const resumeAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/resume/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  getAnalysis: () => api.get('/resume/analysis'),
  getHistory: () => api.get('/resume/history'),
};

export const interviewAPI = {
  start: (data) => api.post('/interview/start', data),
  submitAnswer: (data) => api.post('/interview/submit', data),
  getSummary: (sessionId) => api.get(`/interview/session/${sessionId}/summary`),
  getHistory: () => api.get('/interview/history'),
};

export const analyticsAPI = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getReadiness: () => api.get('/analytics/readiness'),
  getRecommendations: () => api.get('/analytics/recommendations'),
};

export default api;
