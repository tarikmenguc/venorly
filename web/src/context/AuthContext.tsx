"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

// ─── Types ──────────────────────────────────────────────────────────────────

type AuthResult = { error: string | null };

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<AuthResult>;
  signUp: (email: string, password: string) => Promise<AuthResult>;
  signOut: () => Promise<void>;
}

// ─── Context ────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // İlk yüklemede mevcut session'ı al
    supabase.auth.getUser().then(({ data }) => {
      setUser(data.user);
      setLoading(false);
    });

    // Auth değişikliklerini dinle (giriş/çıkış, token yenileme vb.)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string): Promise<AuthResult> => {
    try {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        // Türkçe hata mesajları
        if (error.message.includes("Invalid login credentials"))
          return { error: "E-posta veya şifre hatalı." };
        if (error.message.includes("Email not confirmed"))
          return { error: "E-posta adresin henüz doğrulanmamış." };
        return { error: error.message };
      }
      return { error: null };
    } catch (e: unknown) {
      return { error: e instanceof Error ? e.message : "Beklenmedik bir hata oluştu." };
    }
  };

  const signUp = async (email: string, password: string): Promise<AuthResult> => {
    try {
      const { error } = await supabase.auth.signUp({ email, password });
      if (error) {
        if (error.message.includes("already registered"))
          return { error: "Bu e-posta zaten kayıtlı. Giriş yapmayı dene." };
        return { error: error.message };
      }
      return { error: null };
    } catch (e: unknown) {
      return { error: e instanceof Error ? e.message : "Beklenmedik bir hata oluştu." };
    }
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch (_) { /* sessizce geç */ }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ───────────────────────────────────────────────────────────────────

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth, AuthProvider içinde kullanılmalı");
  return ctx;
}
