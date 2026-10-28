"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  institution_id?: string | null;
  institution_name?: string | null;
  is_active: boolean;
  mfa_enabled: boolean;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, otp?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("satya_access_token");
    const savedUser = localStorage.getItem("satya_user_profile");
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem("satya_access_token");
        localStorage.removeItem("satya_user_profile");
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string, otp?: string) => {
    setIsLoading(true);
    try {
      const data = await apiRequest<{
        access_token: string;
        refresh_token: string;
        role: string;
        full_name: string;
        email: string;
        institution_id?: string;
        institution_name?: string;
      }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, otp_code: otp }),
      });

      localStorage.setItem("satya_access_token", data.access_token);
      localStorage.setItem("satya_refresh_token", data.refresh_token);

      const profile: UserProfile = {
        id: data.email,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        institution_id: data.institution_id,
        institution_name: data.institution_name,
        is_active: true,
        mfa_enabled: false,
      };

      localStorage.setItem("satya_user_profile", JSON.stringify(profile));
      setToken(data.access_token);
      setUser(profile);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("satya_access_token");
    localStorage.removeItem("satya_refresh_token");
    localStorage.removeItem("satya_user_profile");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
