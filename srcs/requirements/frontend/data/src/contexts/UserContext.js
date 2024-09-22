import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api.js';

const UserContext = createContext();

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [avatarVersion, setAvatarVersion] = useState(0);
  const [nicknameVersion, setNicknameVersion] = useState(0);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/authentication/users/me/'); // gets a "user" object
      setUser(response.data.user);
      setIsAuthenticated(true);
      setError(null);
    } catch (err) {
      setUser(null);
      setIsAuthenticated(false);
      setError('Authentication failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const register = async (userData) => {
    const response = await api.post('/authentication/users/', userData);
  };

  const login = async (userData) => {
    const response = await api.post('/authentication/auth/login/', userData);
    if (response.data.message !== "Login successful") {
      throw new Error("Login failed");
    }
    await checkAuth();
  };

  const logout = async () => {
    await api.post('/authentication/auth/logout/');
    setUser(null);
    setIsAuthenticated(false);
    navigate('/logout-success');
    await checkAuth();
  };

  // For any user update
  const updateUser = useCallback((updates) => {
    setUser(prevUser => ({
      ...prevUser,
      ...updates
    }));
  }, []);

  // To force a reload of the avatar image and not use browser cache
  const updateAvatarVersion = useCallback(() => {
    setAvatarVersion(v => v + 1);
  }, []);

  const updateNicknameVersion = useCallback(() => {
    setNicknameVersion(v => v + 1);
  }, []);

  const getAvatarUrl = useCallback(() => {
    if (user?.avatar_url) {
      return `${user.avatar_url}?v=${avatarVersion}`;
    }
    return null;
  }, [user?.avatar_url, avatarVersion]);

  const value = {
    user,
    setUser,
    isAuthenticated,
    loading,
    error,
    login,
    logout,
    checkAuth,
    register,
    updateUser,
    updateAvatarVersion,
    updateNicknameVersion,
    getAvatarUrl
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}
