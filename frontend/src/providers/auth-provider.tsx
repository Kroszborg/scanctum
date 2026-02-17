"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { getToken, getUser, removeToken, setToken, setUser } from "@/lib/auth";
import type { User, LoginResponse } from "@/types/auth";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    const savedUser = getUser();
    if (token && savedUser) {
      setUserState(savedUser as User);
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post<LoginResponse>("/auth/login", { email, password });
    setToken(res.data.access_token);
    setUser(res.data.user);
    setUserState(res.data.user);
    router.push("/dashboard");
  }, [router]);

  const signup = useCallback(async (email: string, password: string, fullName: string) => {
    const res = await api.post<LoginResponse>("/auth/signup", { email, password, full_name: fullName });
    setToken(res.data.access_token);
    setUser(res.data.user);
    setUserState(res.data.user);
    router.push("/dashboard");
  }, [router]);

  const logout = useCallback(() => {
    removeToken();
    setUserState(null);
    router.push("/login");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
