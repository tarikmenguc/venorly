"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * ErrorBoundary — React sınıf bileşeni (hooks desteği olmayan durum için gerekli)
 * Uygulamanın herhangi bir noktasında oluşan render hatalarını yakalar ve
 * kullanıcı dostu bir hata ekranı gösterir.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Production'da Sentry veya benzeri bir servise gönderilebilir
    console.error("[ErrorBoundary] Yakalandı:", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-[60vh] flex items-center justify-center p-8">
          <div className="max-w-md w-full text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 mb-6">
              <AlertTriangle className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Bir şeyler yanlış gitti
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Bu bileşen beklenmedik bir hatayla karşılaştı. Sayfayı yenileyebilir
              veya aşağıdaki butona tıklayarak tekrar deneyebilirsiniz.
            </p>
            {this.state.error && (
              <pre className="text-xs text-left bg-white/5 border border-white/10 rounded-lg p-3 mb-6 overflow-auto max-h-32 text-red-300">
                {this.state.error.message}
              </pre>
            )}
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-white hover:bg-white/10 transition-all"
              >
                <RefreshCw className="w-4 h-4" />
                Tekrar Dene
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 rounded-lg bg-purple-600/80 text-white text-sm hover:bg-purple-600 transition-all"
              >
                Sayfayı Yenile
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
