import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({ baseURL: API_BASE });

// Token management
let accessToken = localStorage.getItem('ja_access') || '';
let refreshToken = localStorage.getItem('ja_refresh') || '';
let onLogout = null;

export function setLogoutHandler(fn) { onLogout = fn; }

export function setTokens(access, refresh) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('ja_access', access);
  localStorage.setItem('ja_refresh', refresh);
}

export function getTokens() {
  return { accessToken, refreshToken };
}

export function clearTokens() {
  accessToken = '';
  refreshToken = '';
  localStorage.removeItem('ja_access');
  localStorage.removeItem('ja_refresh');
}

export function hasTokens() {
  return !!accessToken;
}

// Request interceptor — attach access token
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Response interceptor — auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && refreshToken) {
      original._retry = true;
      try {
        const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        setTokens(data.access_token, data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        clearTokens();
        if (onLogout) onLogout();
      }
    }
    return Promise.reject(error);
  }
);

// ===== Auth =====
export const authAPI = {
  signup: (body) => axios.post(`${API_BASE}/auth/signup`, body),
  login: (body) => axios.post(`${API_BASE}/auth/login`, body),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  googleUrl: () => `${API_BASE}/auth/google`,
};

// ===== Profile =====
export const profileAPI = {
  get: () => api.get('/profile'),
  update: (body) => api.put('/profile', body),
  importResume: (file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post('/profile/import-resume', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ===== Chat =====
export const chatAPI = {
  send: (message, threadId = null, context = null) =>
    api.post('/chat', { message, thread_id: threadId, context }),
};

// ===== Threads =====
export const threadsAPI = {
  list: () => api.get('/threads'),
  create: (title = 'New chat') => api.post('/threads', { title }),
  get: (id) => api.get(`/threads/${id}`),
  delete: (id) => api.delete(`/threads/${id}`),
  updateTitle: (id, title) => api.patch(`/threads/${id}`, { title }),
};

export default api;
