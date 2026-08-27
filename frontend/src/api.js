const API_BASE = '/api/v1';

export async function fetchApi(endpoint, options = {}) {
  const token = localStorage.getItem('career_agent_token');
  const headers = {
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      localStorage.removeItem('career_agent_token');
    }

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorData.detail || `Request failed with status ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Auth
  getMe: () => fetchApi('/auth/me'),
  logout: () => {
    localStorage.removeItem('career_agent_token');
  },
  login: (email, password) => fetchApi('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  }),
  register: (email, password, full_name, phone_number) => fetchApi('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name, phone_number })
  }),
  googleAuth: (data) => fetchApi('/auth/google', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  sendOtp: (email, purpose = 'email_verification') => fetchApi('/auth/send-otp', {
    method: 'POST',
    body: JSON.stringify({ email, purpose })
  }),
  verifyOtp: (email, otp_code, purpose = 'email_verification') => fetchApi('/auth/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ email, otp_code, purpose })
  }),
  forgotPassword: (email) => fetchApi('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email })
  }),
  resetPassword: (email, otp_code, new_password) => fetchApi('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ email, otp_code, new_password })
  }),

  // Dashboard
  getStats: () => fetchApi('/dashboard/stats'),

  // Profile & Resumes
  getProfile: () => fetchApi('/profile'),
  updateProfile: (data) => fetchApi('/profile', {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  getResumes: () => fetchApi('/resumes'),
  uploadResume: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchApi('/resumes/upload', {
      method: 'POST',
      body: formData
    });
  },

  // Preferences
  getPreferences: () => fetchApi('/preferences'),
  updatePreferences: (data) => fetchApi('/preferences', {
    method: 'PUT',
    body: JSON.stringify(data)
  }),

  // Jobs & Discovery
  getJobs: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return fetchApi(`/jobs${query ? '?' + query : ''}`);
  },
  getJob: (id) => fetchApi(`/jobs/${id}`),
  syncJobs: () => fetchApi('/jobs/sync', { method: 'POST' }),

  // Matches & Gap
  getMatches: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return fetchApi(`/matches${query ? '?' + query : ''}`);
  },
  getMatch: (id) => fetchApi(`/matches/${id}`),
  saveMatch: (id) => fetchApi(`/matches/${id}/save`, { method: 'POST' }),
  skipMatch: (id) => fetchApi(`/matches/${id}/skip`, { method: 'POST' }),
  recalculateMatches: () => fetchApi('/matches/recalculate', { method: 'POST' }),

  // Applications & Safety Confirmation Gate
  prepareApplication: (jobId) => fetchApi('/applications/prepare', {
    method: 'POST',
    body: JSON.stringify({ job_id: jobId })
  }),
  confirmApplication: (appId, data) => fetchApi(`/applications/${appId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  getApplications: (status) => fetchApi(`/applications${status ? '?status=' + status : ''}`),
  updateApplicationStatus: (appId, status, notes) => fetchApi(`/applications/${appId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status, notes })
  }),

  // Notifications
  getNotifications: () => fetchApi('/notifications'),
  markNotificationRead: (id) => fetchApi(`/notifications/${id}/read`, { method: 'POST' }),
  markAllNotificationsRead: () => fetchApi('/notifications/read-all', { method: 'POST' }),
};
