import { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("examnest_token");
    if (!token) { setLoading(false); return; }
    authApi.me()
      .then((u) => setUser(u))
      .catch(() => localStorage.removeItem("examnest_token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (data) => {
    const r = await authApi.login(data);
    localStorage.setItem("examnest_token", r.token);
    setUser(r.user);
    return r.user;
  };
  const signup = async (data) => {
    const r = await authApi.signup(data);
    localStorage.setItem("examnest_token", r.token);
    setUser(r.user);
    return r.user;
  };
  const logout = () => {
    localStorage.removeItem("examnest_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
