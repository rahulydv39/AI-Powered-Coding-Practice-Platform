"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { getCurrentUser, loginUser, logoutUser, registerUser } from "./api";
import { UserProfile } from "./types";

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  login: (payload: { email: string; password: string }) => Promise<{ success: boolean; error?: string }>;
  register: (payload: { email: string; password: string; full_name?: string }) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    const res = await getCurrentUser();
    if (res.data) {
      setUser(res.data);
    } else {
      setUser(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    let active = true;
    getCurrentUser().then((res) => {
      if (active) {
        setUser(res.data || null);
        setLoading(false);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const login = async (payload: { email: string; password: string }) => {
    const res = await loginUser(payload);
    if (res.data) {
      setUser(res.data);
      return { success: true };
    }
    return { success: false, error: res.error || "Failed to sign in." };
  };

  const register = async (payload: { email: string; password: string; full_name?: string }) => {
    const res = await registerUser(payload);
    if (res.data) {
      setUser(res.data);
      return { success: true };
    }
    return { success: false, error: res.error || "Failed to create account." };
  };

  const logout = async () => {
    await logoutUser();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
