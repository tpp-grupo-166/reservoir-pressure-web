import { useState, useEffect } from 'react';
import { login as loginService, register as registerService, getCurrentUser, logout as logoutService, type User } from '../services/authService';
import { getToken, removeToken } from '../utils/auth';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (token) {
      getCurrentUser()
        .then((userData) => {
          setUser(userData);
          setIsAuthenticated(true);
        })
        .catch(() => {
          removeToken();
          setIsAuthenticated(false);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    await loginService({ email, password });
    const userData = await getCurrentUser();
    setUser(userData);
    setIsAuthenticated(true);
  };

  const register = async (email: string, password: string) => {
    await registerService({ email, password });
  };

  const logout = () => {
    logoutService();
    setUser(null);
    setIsAuthenticated(false);
  };

  return {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
  };
}
