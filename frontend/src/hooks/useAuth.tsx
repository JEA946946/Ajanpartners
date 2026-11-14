import React, { useState, useEffect, createContext, useContext } from 'react';
import api from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  /** true = logget ind; { mfaToken } = trin 2 (to-faktor-kode) mangler. */
  login: (username: string, password: string) => Promise<boolean | { mfaToken: string }>;
  verifyMfa: (mfaToken: string, code: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('bk_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('bk_token');
    if (storedToken) {
      try {
        const payload = JSON.parse(atob(storedToken.split('.')[1]));
        if (payload.exp * 1000 > Date.now()) {
          setToken(storedToken);
          // Fetch profile
          api.get('/auth/profile').then((res: any) => {
            if (res.data.success) setUser(res.data.data.user);
          }).catch((err: any) => {
            // Kun en afvist token (401) logger ud. Andre fejl (netværk, 403, 500) gør ikke:
            // brugeren bliver logget ind, og siden prøver igen.
            if (err?.response?.status === 401) {
              localStorage.removeItem('bk_token');
              localStorage.removeItem('bk_refreshToken');
              setToken(null);
            } else {
              try {
                const p = JSON.parse(atob(storedToken.split('.')[1]));
                setUser({ id: String(p.userId ?? ''), username: '', email: '', first_name: '', last_name: '' });
              } catch { /* ignore */ }
            }
          }).finally(() => setLoading(false));
          return;
        } else {
          // Token expired — try refresh
          const refreshTk = localStorage.getItem('bk_refreshToken');
          if (refreshTk) {
            api.post('/auth/refresh', { refreshToken: refreshTk }).then((res: any) => {
              if (res.data.success) {
                const newToken = res.data.data.token;
                localStorage.setItem('bk_token', newToken);
                if (res.data.data.refreshToken) {
                  localStorage.setItem('bk_refreshToken', res.data.data.refreshToken);
                }
                setToken(newToken);
                return api.get('/auth/profile');
              }
              throw new Error('Refresh failed');
            }).then((res: any) => {
              if (res.data.success) setUser(res.data.data.user);
            }).catch(() => {
              localStorage.removeItem('bk_token');
              localStorage.removeItem('bk_refreshToken');
              setToken(null);
            }).finally(() => setLoading(false));
            return;
          }
          localStorage.removeItem('bk_token');
          localStorage.removeItem('bk_refreshToken');
          setToken(null);
        }
      } catch {
        localStorage.removeItem('bk_token');
        setToken(null);
      }
    }
    setLoading(false);
  }, []);

  const acceptTokens = (data: any) => {
    setUser(data.user);
    setToken(data.token);
    localStorage.setItem('bk_token', data.token);
    if (data.refreshToken) localStorage.setItem('bk_refreshToken', data.refreshToken);
  };

  const verifyMfa = async (mfaToken: string, code: string): Promise<boolean> => {
    setLoading(true);
    try {
      const response = await api.post('/auth/mfa/verify', { mfa_token: mfaToken, code });
      if (response.data.success) {
        acceptTokens(response.data.data);
        return true;
      }
      return false;
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string): Promise<boolean | { mfaToken: string }> => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', { username, password });
      if (response.data.success && response.data.data.mfa_required) {
        return { mfaToken: response.data.data.mfa_token };
      }
      if (response.data.success) {
        setUser(response.data.data.user);
        setToken(response.data.data.token);
        localStorage.setItem('bk_token', response.data.data.token);
        if (response.data.data.refreshToken) {
          localStorage.setItem('bk_refreshToken', response.data.data.refreshToken);
        }
        return true;
      }
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('bk_token');
    localStorage.removeItem('bk_refreshToken');
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!user && !!token, login, verifyMfa, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
