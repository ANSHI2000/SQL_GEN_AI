import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const response = await authAPI.getProfile();
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('access_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        await loadUser();
      }
      return response.data;
    } catch (error) {
      // Re-throw with proper error info
      const errorData = error.response?.data;
      throw {
        ...error,
        isVerifyError: errorData?.detail === 'Please verify your email first',
        email: email
      };
    }
  };

  const signup = async (data) => {
    const response = await authAPI.signup(data);
    return response.data;
  };

  const verifyOTP = async (data) => {
    const response = await authAPI.verifyOTP(data);
    return response.data;
  };

  const logout = () => {
    authAPI.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, verifyOTP, logout }}>
      {children}
  
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};