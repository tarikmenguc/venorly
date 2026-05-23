"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Loader2, Mail, Lock, Sparkles, Eye, EyeOff } from "lucide-react";

export default function SignInPage() {
  const router = useRouter();
  const { signIn } = useAuth();

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const { error } = await signIn(email, password);
      if (error) {
        setError(error);
        return;
      }
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Beklenmedik bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      {/* Soft gradient glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary/20 border border-primary/30 mb-4">
            <Sparkles size={22} className="text-primary" />
          </div>
          <h1 className="text-2xl font-bold text-white">Hoş Geldin</h1>
          <p className="text-muted-foreground text-sm mt-1">Venorly'ye giriş yap</p>
        </div>

        {/* Form Card */}
        <div className="bg-card/60 backdrop-blur-md border border-border/60 rounded-2xl p-6 shadow-xl">
          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">

            {/* Email */}
            <div className="space-y-1.5">
              <label className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                E-posta
              </label>
              <div className="relative">
                <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  placeholder="ornek@mail.com"
                  className="w-full pl-9 pr-4 py-2.5 bg-muted/40 border border-border/60 rounded-xl text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/60 focus:bg-muted/60 transition-colors"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                Şifre
              </label>
              <div className="relative">
                <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full pl-9 pr-10 py-2.5 bg-muted/40 border border-border/60 rounded-xl text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/60 focus:bg-muted/60 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : null}
              {loading ? "Giriş yapılıyor..." : "Giriş Yap"}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border/40" />
            </div>
            <div className="relative flex justify-center">
              <span className="px-3 bg-card/60 text-xs text-muted-foreground">veya</span>
            </div>
          </div>

          <p className="text-center text-sm text-muted-foreground">
            Hesabın yok mu?{" "}
            <Link href="/sign-up" className="text-primary hover:underline font-medium">
              Kayıt Ol
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-muted-foreground/50 mt-6">
          <Link href="/" className="hover:text-muted-foreground transition-colors">
            ← Ana sayfaya dön
          </Link>
        </p>
      </div>
    </div>
  );
}
