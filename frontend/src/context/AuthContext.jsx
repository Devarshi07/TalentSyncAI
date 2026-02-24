import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  authAPI, setTokens, clearTokens, hasTokens, setLogoutHandler,
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(async () => {
    try { await authAPI.logout(); } catch {}
    clearTokens();
    setUser(null);
  }, []);

  useEffect(() => {
    setLogoutHandler(() => setUser(null));

    // Check OAuth callback params
    const params = new URLSearchParams(window.location.search);
    const at = params.get('access_token');
    const rt = params.get('refresh_token');
    if (at && rt) {
      setTokens(at, rt);
      window.history.replaceState({}, '', '/');
    }

    if (hasTokens()) {
      authAPI.me()
        .then(({ data }) => setUser(data))
        .catch(() => { clearTokens(); setUser(null); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const { data } = await authAPI.login({ username, password });
    setTokens(data.access_token, data.refresh_token);
    setUser(data.user);
    return data.user;
  };

  const signup = async (username, email, password) => {
    const { data } = await authAPI.signup({ username, email, password });
    setTokens(data.access_token, data.refresh_token);
    setUser(data.user);
    return data.user;
  };

  const googleLogin = () => {
    window.location.href = authAPI.googleUrl();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, googleLogin }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
