"use client";

import { useState, useRef, useEffect } from "react";
import {
  MessageSquare, X, Send, Loader2, Sparkles,
  DollarSign, Target, Wrench, BarChart3, Swords
} from "lucide-react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatPanelProps {
  scanId: string | null;
  reportContext?: string;
}

const QUICK_PROMPTS = [
  { icon: DollarSign, label: "Fiyatlandırma stratejisi öner", prompt: "Bu fikir için en uygun fiyatlandırma stratejisi ne olmalı? Freemium mu, aylık abonelik mi, kullanım başına ücret mi?" },
  { icon: Target, label: "İlk 100 müşteriyi nasıl bulurum?", prompt: "Bu ürün için ilk 100 müşteriyi nasıl bulabilirim? Hangi kanalları kullanmalıyım?" },
  { icon: Wrench, label: "Teknik mimari nasıl olmalı?", prompt: "Bu fikri geliştirmek için teknik mimari nasıl olmalı? Hangi teknolojileri kullanmalıyım?" },
  { icon: BarChart3, label: "Pazar büyüklüğünü tahmin et", prompt: "Bu pazarın toplam büyüklüğü (TAM/SAM/SOM) ne olabilir? Rakamlarla tahmin et." },
  { icon: Swords, label: "Rakiplerden nasıl farklılaşırım?", prompt: "Rakiplerin zayıf noktaları neler ve ben nasıl farklılaşabilirim? Unfair advantage öner." },
];

export function ChatPanel({ scanId, reportContext }: ChatPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [remaining, setRemaining] = useState(15);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load chat history when panel opens
  useEffect(() => {
    if (isOpen && scanId && !historyLoaded) {
      loadHistory();
    }
  }, [isOpen, scanId]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  async function loadHistory() {
    if (!scanId) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/chat/${scanId}`);
      const data = await res.json();
      if (data.messages) {
        setMessages(data.messages.map((m: any) => ({ role: m.role, content: m.content })));
        const userMsgCount = data.messages.filter((m: any) => m.role === "user").length;
        setRemaining(data.limit - userMsgCount);
      }
      setHistoryLoaded(true);
    } catch (e) {
      console.error("Chat history error:", e);
      setHistoryLoaded(true);
    }
  }

  async function sendMessage(text: string) {
    if (!text.trim() || !scanId || isStreaming || remaining <= 0) return;

    const userMsg: ChatMessage = { role: "user", content: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    // Add empty assistant message placeholder
    setMessages(prev => [...prev, { role: "assistant", content: "" }]);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_id: scanId, message: text.trim() }),
      });

      if (res.status === 429) {
        const errorData = await res.json();
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: `⚠️ ${errorData.error}` };
          return updated;
        });
        setRemaining(0);
        setIsStreaming(false);
        return;
      }

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const events = chunk.split("\n\n");

        for (const ev of events) {
          if (ev.startsWith("data: ")) {
            try {
              const data = JSON.parse(ev.replace("data: ", ""));
              if (data.token) {
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: "assistant",
                    content: updated[updated.length - 1].content + data.token,
                  };
                  return updated;
                });
              }
              if (data.done) {
                setRemaining(data.remaining);
              }
              if (data.error) {
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: "assistant", content: `❌ Hata: ${data.error}` };
                  return updated;
                });
              }
            } catch {}
          }
        }
      }
    } catch (error) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: "❌ Bağlantı hatası. Backend çalışıyor mu?" };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  }

  if (!scanId) return null;

  return (
    <>
      {/* FAB Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-5 py-3 rounded-full bg-gradient-to-r from-purple-600 to-violet-500 text-white font-semibold shadow-[0_0_30px_-5px_rgba(168,85,247,0.5)] hover:scale-105 transition-all"
        >
          <MessageSquare className="w-5 h-5" />
          AI ile Tartış
        </button>
      )}

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Panel */}
      <div
        className={`fixed top-0 right-0 h-full w-full sm:w-[420px] bg-background border-l border-white/10 z-50 flex flex-col shadow-2xl transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-gradient-to-r from-purple-950/20 to-transparent">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-purple-600 to-violet-500">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">AI Fikir Danışmanı</h3>
              <p className="text-[11px] text-muted-foreground">
                {remaining > 0 ? `${remaining} mesaj hakkınız kaldı` : "Mesaj limitiniz doldu"}
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 rounded-lg hover:bg-white/5 transition-colors"
          >
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 && !isStreaming && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground text-center py-4">
                Rapor hakkında sormak istediğin bir şey var mı? 👇
              </p>
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(qp.prompt)}
                  className="w-full flex items-center gap-3 p-3 rounded-xl bg-card border border-white/5 hover:border-purple-500/20 hover:bg-white/[0.02] transition-all text-left group"
                >
                  <qp.icon className="w-4 h-4 text-purple-400 flex-shrink-0 group-hover:scale-110 transition-transform" />
                  <span className="text-sm text-white/70 group-hover:text-white transition-colors">{qp.label}</span>
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-purple-600 to-violet-500 text-white rounded-br-md"
                    : "bg-card border border-white/5 text-white/85 rounded-bl-md"
                }`}
              >
                {msg.content || (
                  <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-white/5 bg-background">
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
              placeholder={remaining > 0 ? "Bir soru sor..." : "Mesaj limitiniz doldu"}
              disabled={isStreaming || remaining <= 0}
              className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-white/30 text-sm focus:outline-none focus:ring-1 focus:ring-purple-500/50 disabled:opacity-50"
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isStreaming || remaining <= 0}
              className="p-3 rounded-xl bg-gradient-to-r from-purple-600 to-violet-500 text-white hover:scale-105 transition-all disabled:opacity-30 disabled:hover:scale-100"
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
          <div className="flex justify-center mt-2">
            <span className="text-[10px] text-muted-foreground/50">
              Powered by Startup Idea Finder AI
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
