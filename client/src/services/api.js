import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:5000/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("verdant_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
};

export const profileAPI = {
  get: () => api.get("/profile/get"),
  update: (data) => api.put("/profile/update", data),
  uploadPhoto: (formData) =>
    api.post("/profile/photo", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

export const scannerAPI = {
  upload: (formData) =>
    api.post("/scanner/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  history: () => api.get("/scanner/history"),
  clearHistory: () => api.delete("/scanner/history"),
};

export const plantsAPI = {
  getAll: () => api.get("/plants"),
  create: (data) => api.post("/plants", data),
  update: (id, data) => api.put(`/plants/${id}`, data),
  remove: (id) => api.delete(`/plants/${id}`),
};

export const reportAPI = {
  submit: (data) => api.post("/report", data),
};

export default api;
