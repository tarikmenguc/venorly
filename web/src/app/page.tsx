"use client";

import { useState } from "react";
import { GradientDots } from "@/components/ui/gradient-dots";
import { NavBar } from "@/components/ui/tubelight-navbar";
import { TextLoop } from "@/components/ui/text-loop";
import { Home, Lightbulb, Search, Settings, LineChart, Cpu, Sparkles, Loader2, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function HomeDashboard() {
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentNode, setCurrentNode] = useState("");
  const [report, setReport] = useState("");
  const [leads, setLeads] = useState<any[]>([]);
  const [mode, setMode] = useState("discover");
  const [isCreatingWaitlist, setIsCreatingWaitlist] = useState(false);

  const navItems = [
    { name: "Keşfet", url: "#", icon: Home, mode: "discover" },
    { name: "Derin Analiz", url: "#", icon: Cpu, mode: "deep" },
    { name: "Orkestratör", url: "#", icon: Users, mode: "orchestrate" },
    { name: "Rakip Ara", url: "#", icon: Search, mode: "reverse" },
    { name: "Trendler", url: "#", icon: LineChart, mode: "trends" },
  ];

  const handleScan = async () => {
    if (!category) {
      alert("Lütfen önce arama kutusuna bir konu veya rakip girin (Örn: AI Agents)");
      return;
    }
    setLoading(true);
    setCurrentNode("Agent başlatılıyor...");
    setReport("");
    setLeads([]);

    try {
      const response = await fetch("http://localhost:8000/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Use the current mode state, default to the currently selected mode
        body: JSON.stringify({ mode: mode, category }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const events = chunk.split("\n\n");

        for (const ev of events) {
          if (ev.startsWith("data: ")) {
            try {
              const dataStr = ev.replace("data: ", "");
              if (!dataStr) continue;
              const data = JSON.parse(dataStr);

              if (data.status === "done") {
                setLoading(false);
                setCurrentNode("Analiz Tamamlandı ✨");
              } else if (data.error) {
                setCurrentNode(`Hata: ${data.error} `);
                setLoading(false);
              } else if (data.node) {
                setCurrentNode(`İşlem: ${data.node}...`);

                if (data.state) {
                  const finalOutput = data.state.investment_memo || data.state.final_report;
                  if (finalOutput) {
                    setReport(finalOutput);
                  }
                  if (data.state.buyer_leads && data.state.buyer_leads.length > 0) {
                    setLeads(data.state.buyer_leads);
                  }
                }
              }
            } catch (e) {
              // Ignore parse errors on incomplete chunks
            }
          }
        }
      }
    } catch (error: any) {
      setCurrentNode("Bağlantı Hatası: Lütfen arkada FastAPI'nin çalıştığından emin ol.");
      setLoading(false);
    }
  };

  const handleCreateWaitlist = async () => {
    if (!report) return;
    setIsCreatingWaitlist(true);
    try {
      // Çok basit bir regex ile raporun içinden başlığı ve fikri çekiyoruz
      const titleMatch = report.match(/🔥 NİŞ FIRSAT: (.+)/);
      const title = titleMatch ? titleMatch[1].replace(/━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━/g, '').trim() : `${category} için AI Otomasyonu`;

      const audienceMatch = report.match(/🎯 Odaklanılacak B2B Niş: (.+)/);
      const audience = audienceMatch ? audienceMatch[1].trim() : "B2B Profesyoneller";

      const summaryMatch = report.match(/💡 Fırsat Özeti:([\s\S]*?)(🔗|━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━|$)/);
      let description = "Manuel saatler alan angaryayı tek tıklamaya indiren yapay zeka çözümü.";
      if (summaryMatch && summaryMatch[1]) {
        description = summaryMatch[1].replace(/\[|\]/g, '').trim();
      }

      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, target_audience: audience })
      });

      const data = await res.json();
      if (data.id) {
        window.open(`/waitlist/${data.id}`, '_blank');
      } else {
        alert("Waitlist oluşturulamadı.");
      }
    } catch (e) {
      alert("Hata oluştu.");
    } finally {
      setIsCreatingWaitlist(false);
    }
  };

  return (
    <main className="relative flex min-h-screen w-full flex-col bg-background text-foreground overflow-x-hidden">
      {/* Arka plan animasyonu tıklamaları engellememesi için pointer-events-none */}
      <div className="absolute inset-0 pointer-events-none z-[-1]">
        <GradientDots duration={40} dotSize={6} spacing={12} className="opacity-40 w-full h-full pointer-events-none" />
      </div>

      {/* Navbar'ı doğrudan çağırıyoruz ve mode değiştiğinde her şeyi sıfırlıyoruz */}
      <NavBar items={navItems} onTabChange={(newMode: string) => {
        setMode(newMode);
        setReport("");
        setLeads([]);
        setCategory("");
        setCurrentNode("");
      }} activeMode={mode} />

      {/* İçerik alanının tıklanabilir olması için z-10 */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 pt-24 pb-12 w-full max-w-5xl mx-auto">

        {!report && !loading && (
          <div className="flex flex-col items-center justify-center -mt-20">
            <Badge variant="outline" className="mb-6 backdrop-blur-md bg-white/5 border-white/10 px-4 py-1 text-sm font-medium hover:bg-white/10 transition-colors">
              <Sparkles className="w-4 h-4 mr-2" /> V4 Deep Research Engine Live
            </Badge>

            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-center max-w-4xl leading-tight">
              Find your next{" "}
              <br className="md:hidden" />
              <span className="text-primary inline-flex">
                <TextLoop interval={3}>
                  <span>Micro-SaaS.</span>
                  <span>AI App.</span>
                  <span>Deep Tech.</span>
                  <span>Unicorn.</span>
                </TextLoop>
              </span>
            </h1>

            <p className="mt-6 max-w-2xl text-center text-lg text-muted-foreground/80 font-medium">
              Zero-cost market intelligence and reasoning engine.
              Discover profitable niches before they explode.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row gap-4 w-full max-w-lg relative z-20">
              <input
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder={mode === "reverse" ? "Örn: Lumen5..." : "Örn: Video Generation..."}
                className="flex-1 px-6 py-4 rounded-full bg-white/5 border border-white/10 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-primary backdrop-blur-md"
              />
              <button
                onClick={handleScan}
                className="px-8 py-4 rounded-full bg-primary text-primary-foreground font-semibold text-lg shadow-[0_0_40px_-10px_rgba(var(--primary),0.8)] hover:scale-105 transition-all duration-300 whitespace-nowrap cursor-pointer z-30"
              >
                {mode === "reverse" ? "Rakip Analizi Başlat" : mode === "deep" ? "Derin Analiz" : "Hızlı Tarama"}
              </button>
            </div>
          </div>
        )}

        {(loading || report) && (
          <div className="w-full flex-1 flex flex-col items-center animate-in fade-in duration-500">
            <div className="w-full max-w-4xl p-6 rounded-2xl bg-black/40 border border-white/10 backdrop-blur-xl mb-8 flex items-center justify-between">
              <div className="flex items-center gap-4">
                {loading ? (
                  <Loader2 className="w-6 h-6 text-primary animate-spin" />
                ) : (
                  <Sparkles className="w-6 h-6 text-primary" />
                )}
                <div>
                  <h3 className="font-semibold text-white">Analiz Durumu</h3>
                  <p className="text-sm text-white/60">{currentNode}</p>
                </div>
              </div>
              <Badge variant="outline" className="border-primary/50 text-primary bg-primary/10">
                {mode === 'deep' ? '🧠 Deep Research' : '⚡ Quick Discover'}
              </Badge>
            </div>

            {report && (
              <div className="w-full max-w-4xl p-8 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-2xl shadow-2xl overflow-y-auto prose prose-invert prose-primary mx-auto">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {report}
                </ReactMarkdown>
              </div>
            )}

            {leads.length > 0 && (
              <div className="w-full max-w-4xl p-8 rounded-2xl bg-black/60 border border-white/10 backdrop-blur-2xl shadow-2xl mt-8 mx-auto animate-in slide-in-from-bottom-5">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  Hazır Alıcılar (Friction Economy Leads)
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-white/10">
                        <th className="pb-3 px-4 font-medium text-white/60">Platform</th>
                        <th className="pb-3 px-4 font-medium text-white/60">Gönderi/Ağrı Noktası</th>
                        <th className="pb-3 px-4 font-medium text-white/60 w-1/3">Satış / DM Şablonu</th>
                      </tr>
                    </thead>
                    <tbody>
                      {leads.map((lead, idx) => (
                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                          <td className="py-4 px-4 align-top">
                            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
                              {lead.source}
                            </Badge>
                          </td>
                          <td className="py-4 px-4 align-top text-sm text-white/80">
                            <p className="font-semibold mb-1">{lead.title}</p>
                            <p className="text-white/50 line-clamp-2">{lead.desc}</p>
                            {lead.url && (
                              <a href={lead.url} target="_blank" rel="noreferrer" className="text-primary hover:underline mt-2 inline-block">Sinyale Git &rarr;</a>
                            )}
                          </td>
                          <td className="py-4 px-4 align-top">
                            <div className="bg-white/5 p-3 rounded-lg border border-white/10 text-sm text-white/90 font-mono">
                              {lead.sales_pitch || "Şablon oluşturulamadı."}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {report && !loading && (
              <div className="w-full max-w-4xl p-8 rounded-2xl bg-black/40 border border-emerald-500/20 backdrop-blur-2xl shadow-2xl mt-8 mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 animate-in slide-in-from-bottom-5">
                <div>
                  <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                    🚀 Bu Fikri Doğrulamak İster Misin?
                  </h3>
                  <p className="text-white/60 text-sm max-w-lg">
                    Sıfır kod yazmadan bu Micro-SaaS fikri için anında şık bir "Erken Erişim" (Waitlist) sayfası oluştur ve müşterilerden mail toplamaya başla.
                  </p>
                </div>
                <button
                  onClick={handleCreateWaitlist}
                  disabled={isCreatingWaitlist}
                  className="px-8 py-4 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold transition-all flex items-center gap-2 whitespace-nowrap disabled:opacity-50"
                >
                  {isCreatingWaitlist ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                  {isCreatingWaitlist ? "Sayfa Kuruluyor..." : "Doğrulama Sayfası Oluştur"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
