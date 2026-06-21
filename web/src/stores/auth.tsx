import React, { createContext, useCallback, useContext, useMemo, useState } from "react";

interface Officer {
  id: string;
  telegram_id: number;
  role: string;
  display_name: string | null;
  is_active: boolean;
}

interface AuthState {
  token: string | null;
  officer: Officer | null;
}

interface AuthContextType extends AuthState {
  login: (telegramId: number, token: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isSuperAdmin: boolean;
  isAnalyst: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = "secadmin_token";

function loadToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>(() => ({
    token: loadToken(),
    officer: null,
  }));

  const login = useCallback(async (telegramId: number, rawToken: string) => {
    const response = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ telegram_id: telegramId, token: rawToken }),
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

    const data = await response.json();
    saveToken(data.access_token);
    setState({ token: data.access_token, officer: data.officer });
  }, []);

  const logout = useCallback(async () => {
    const token = state.token;
    if (token) {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
    clearToken();
    setState({ token: null, officer: null });
  }, [state.token]);

  const value = useMemo(
    () => ({
      ...state,
      login,
      logout,
      isAuthenticated: state.token !== null,
      isSuperAdmin: state.officer?.role === "super_admin",
      isAnalyst:
        state.officer?.role === "super_admin" ||
        state.officer?.role === "analyst" ||
        state.officer?.role === "responder",
    }),
    [state, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
