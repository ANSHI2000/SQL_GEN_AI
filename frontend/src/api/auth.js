import api from './api';

export const authAPI = {
  signup: (data) => api.post('/api/signup', data),
  resendOTP: (data) => api.post('/api/resend-otp', data),
  login: (data) => api.post('/api/login', data),
  verifyOTP: (data) => api.post('/api/verify-otp', data),
  getProfile: () => api.get('/api/profile'),
  logout: () => {
    localStorage.removeItem('access_token');
  }
};

export const databaseAPI = {
  testConnection: (data) => api.post('/api/database/test-connection', data),
  connect: (data) => api.post('/api/database/connect', data),
  list: () => api.get('/api/database/list'),
  remove: (id) => api.delete(`/api/database/remove/${id}`),
  executeDirect: (data) => api.post('/api/database/execute-direct', data),
  executeSaved: (data) => api.post('/api/database/execute-saved', data),
};

export const schemaAPI = {
  read: (connectionId, refresh = false) => 
    api.get(`/api/schema/read/${connectionId}?refresh=${refresh}`),
  readDirect: (data) => api.post('/api/schema/read-direct', data),
  summary: (connectionId) => 
    api.get(`/api/schema/summary/${connectionId}`),
};

// ✅ Updated to use HuggingFace endpoints
export const geminiAPI = {
  generateSQL: (data) => api.post('/api/huggingface/generate-sql', data),  // Changed
  explainQuery: (data) => api.post('/api/huggingface/explain-query', data), // Changed
};

export const queryAPI = {
  preview: (data) => api.post('/api/query/preview', data),
  execute: (data) => api.post('/api/query/execute', data),
  history: () => api.get('/api/query/history'),
};

export const auditAPI = {
  getLogs: (params) => api.get('/api/audit/logs', { params }),
  getConnectionAccess: (params) => api.get('/api/audit/connection-access', { params }),
};