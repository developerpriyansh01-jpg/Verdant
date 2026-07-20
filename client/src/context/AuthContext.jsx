import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { authAPI, profileAPI } from "../services/api";

const AuthContext = createContext(null);

const DEFAULT_AVATAR =
  "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=100&h=100";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchProfile = useCallback(async () => {
    const token = localStorage.getItem("verdant_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const { data } = await profileAPI.get();
      if (data.success && data.user) {
        setUser(data.user);
        return data.user;
      }
    } catch {
      localStorage.removeItem("verdant_token");
      setUser(null);
    }
    setLoading(false);
    return null;
  }, []);

  useEffect(() => {
    fetchProfile().finally(() => setLoading(false));
  }, [fetchProfile]);

  const login = async (username, password) => {
    const { data } = await authAPI.login({ username, password });
    if (!data.success) throw new Error(data.error || "Authentication failed");
    localStorage.setItem("verdant_token", data.token);
    setUser(data.user);
    toast.success("Welcome back! Loading dashboard...");
    navigate("/");
  };

  const register = async (payload) => {
    const { data } = await authAPI.register(payload);
    if (!data.success) throw new Error(data.error || "Registration failed");
    toast.success("Profile created successfully! Redirecting to login...");
    navigate("/login");
  };

  const logout = () => {
    localStorage.removeItem("verdant_token");
    setUser(null);
    toast("Logged out successfully!", { icon: "ℹ️" });
    setTimeout(() => navigate("/login"), 800);
  };

  const updateUser = (updated) => {
    setUser(updated);
  };

  const getPhotoUrl = () => {
    if (user?.photo_url) {
      if (user.photo_url.startsWith("http")) return user.photo_url;
      return `${import.meta.env.VITE_API_URL?.replace("/api", "") || "http://localhost:5000"}${user.photo_url}`;
    }
    return DEFAULT_AVATAR;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        fetchProfile,
        updateUser,
        getPhotoUrl,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
