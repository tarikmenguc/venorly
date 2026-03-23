"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search, Brain, Bot, RefreshCw, TrendingUp,
  Sparkles, Globe, MessageSquare, Code, ShoppingBag,
  Zap, BarChart3, FileText, Users, ArrowRight,
  ChevronDown, ChevronUp, Lightbulb
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

const modes = [
  {
    icon: Search,
    name: "Keşfet (Discover)",
    color: "from-blue-500 to-cyan-400",
    badge: "Hızlı",
    time: "~30 saniye",
    desc: "Girdiğin kategoride HuggingFace modellerini, Reddit şikayetlerini ve pazar boşluklarını tarayarak anında Micro-SaaS fırsatlarını listeler.",
    details: [
      "HuggingFace'den trend modelleri çeker",
      "Reddit & forum şikayetlerini analiz eder",
      "Otomatik skor ve fizibilite değerlendirmesi yapar",
      "3 farklı fırsat önerisi üretir"
    ]
  },
  {
    icon: Brain,
    name: "Derin Analiz (Deep Research)",
    color: "from-purple-500 to-violet-400",
    badge: "Kapsamlı",
    time: "~2 dakika",
    desc: "5+ aşamalı araştırma pipeline'ı ile pazar boyutu, rakip analizi, n8n/Make.com otomasyon sinyalleri ve Product Hunt boşluklarını derinlemesine inceler.",
    details: [
      "Web araştırması + otomasyon istihbaratı",
      "Product Hunt boşluk analizi",
      "Yatırımcı kalitesinde Investment Memo üretir",
      "B2B müşteri adaylarını (buyer leads) bulur"
    ]
  },
  {
    icon: Bot,
    name: "Orkestratör (Multi-Agent)",
    color: "from-emerald-500 to-green-400",
    badge: "Premium",
    time: "~3 dakika",
    desc: "3 uzman AI ajanı (Araştırma, Analist, Satış) koordineli çalışarak en kapsamlı raporu üretir. Waitlist sayfası bile otomatik oluşturur.",
    details: [
      "Araştırma Ajanı: Veri toplama ve sinyal tespiti",
      "Analist Ajanı: Pazar değerlendirmesi ve VC tarzı memo",
      "GTM Ajanı: DM şablonları ve satış stratejisi",
      "Otomatik Waitlist sayfası oluşturma"
    ]
  },
  {
    icon: RefreshCw,
    name: "Rakip Analizi (Reverse)",
    color: "from-orange-500 to-amber-400",
    badge: "Stratejik",
    time: "~1 dakika",
    desc: "Bir rakip ismi girdiğinde, onun zayıf noktalarını, müşteri şikayetlerini ve 'disruption' fırsatlarını tespit eder.",
    details: [
      "Rakibin güçlü/zayıf yönlerini analiz eder",
      "Müşteri şikayetlerini toplar",
      "AI model eşleştirme ile disruption stratejisi önerir",
      "Detaylı karşı strateji raporu üretir"
    ]
  },
  {
    icon: TrendingUp,
    name: "Trend Raporu",
    color: "from-pink-500 to-rose-400",
    badge: "Vizyon",
    time: "~30 saniye",
    desc: "HuggingFace ve pazar verilerini analiz ederek önümüzdeki 6 ayın AI trendlerini ve gözden kaçan fırsatları raporlar.",
    details: [
      "Yükselen dalga: Neler popüler?",
      "Sessizce büyüyenler: Gözden kaçan fırsatlar",
      "6 aylık tahmin ve öneriler",
      "Sektörel kırılım analizi"
    ]
  }
];

const dataSources = [
  { icon: Code, name: "HuggingFace", desc: "50K+ AI model trend verileri" },
  { icon: MessageSquare, name: "Reddit & Forumlar", desc: "Gerçek kullanıcı şikayetleri ve ihtiyaçları" },
  { icon: ShoppingBag, name: "Product Hunt", desc: "Top ürünlerin boşluk analizi" },
  { icon: Zap, name: "n8n & Make.com", desc: "Otomasyon talepleri ve iş akışı sinyalleri" },
  { icon: Users, name: "Upwork & Freelancer", desc: "B2B hizmet talepleri ve bütçeler" },
  { icon: Globe, name: "Web Araştırması", desc: "Tavily ile derin internet taraması" },
];

const faqs = [
  { q: "Bu araç kimler için?", a: "SaaS girişimcileri, indie hackerlar, ürün yöneticileri ve yatırımcılar için. Micro-SaaS fırsatı arayan herkes kullanabilir." },
  { q: "Gerçekten ücretsiz mi?", a: "Evet! Günlük kullanım limitleri dahilinde tamamen ücretsizdir. Keşfet modu için günde 3, Derin Analiz için günde 1 hak tanınır." },
  { q: "Veriler ne kadar güncel?", a: "Her tarama, o anda canlı veri toplar. HuggingFace modelleri, Reddit gönderileri ve forum tartışmaları gerçek zamanlıdır." },
  { q: "Hangi AI modelleri kullanılıyor?", a: "Groq üzerinde Llama serisi, Google Gemini Embedding 2 ve çoklu LLM fallback sistemi kullanılmaktadır." },
];

export default function FeaturesPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 bg-gradient-to-b from-purple-900/10 via-transparent to-transparent" />
        <div className="max-w-5xl mx-auto px-6 py-24 text-center relative z-10">
          <Badge variant="outline" className="mb-6 bg-white/5 border-white/10 px-4 py-1 text-sm">
            <Sparkles className="w-4 h-4 mr-2" /> Yapay Zeka Destekli Pazar İstihbaratı
          </Badge>
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight">
            Kârlı Startup Fikirleri
            <br />
            <span className="bg-gradient-to-r from-purple-400 via-violet-400 to-blue-400 bg-clip-text text-transparent">
              Herkes Bulmadan Önce Keşfet
            </span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            6 farklı veri kaynağından toplanan sinyalleri, çoklu AI ajanları ile analiz ederek
            validasyon yapılmış Micro-SaaS fırsatlarını ve hazır müşteri adaylarını saniyeler içinde sunar.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/"
              className="px-8 py-4 rounded-full bg-gradient-to-r from-purple-600 to-violet-500 text-white font-semibold text-lg shadow-[0_0_40px_-10px_rgba(168,85,247,0.5)] hover:scale-105 transition-all inline-flex items-center gap-2"
            >
              Hemen Dene <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/dashboard"
              className="px-8 py-4 rounded-full bg-white/5 border border-white/10 text-white font-semibold text-lg hover:bg-white/10 transition-all"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 border-b border-white/5">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-4">Nasıl Çalışır?</h2>
          <p className="text-center text-muted-foreground mb-12 max-w-xl mx-auto">
            3 basit adımda pazar fırsatını keşfet
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { step: "1", title: "Konu Gir", desc: "İlgilendiğin sektörü veya teknolojiyi yaz. Örn: 'Video Generation', 'Invoice Automation'", icon: Lightbulb, color: "text-blue-400" },
              { step: "2", title: "AI Analiz Eder", desc: "Çoklu ajanlar 6+ kaynaktan veri toplayıp derin araştırma yapar. Fırsatları skorlar.", icon: Brain, color: "text-purple-400" },
              { step: "3", title: "Rapor Al", desc: "Validasyon yapılmış fikirler, hazır müşteri adayları ve DM şablonları ile harekete geç.", icon: FileText, color: "text-emerald-400" },
            ].map((item) => (
              <div key={item.step} className="relative rounded-2xl bg-card border border-white/5 p-8 text-center hover:border-white/15 transition-all group">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-violet-500 flex items-center justify-center text-sm font-bold text-white shadow-lg">
                  {item.step}
                </div>
                <item.icon className={`w-10 h-10 ${item.color} mx-auto mt-4 mb-4 group-hover:scale-110 transition-transform`} />
                <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Analysis Modes */}
      <section className="py-20 border-b border-white/5">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-4">5 Analiz Modu</h2>
          <p className="text-center text-muted-foreground mb-12 max-w-xl mx-auto">
            Her biri farklı bir ihtiyaca özel tasarlanmış güçlü araştırma motorları
          </p>
          <div className="space-y-4">
            {modes.map((mode, idx) => (
              <div
                key={idx}
                className="rounded-2xl bg-card border border-white/5 overflow-hidden hover:border-white/10 transition-all"
              >
                <div className="p-6 flex items-start gap-5">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${mode.color} flex-shrink-0`}>
                    <mode.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2 flex-wrap">
                      <h3 className="text-lg font-bold text-white">{mode.name}</h3>
                      <Badge variant="outline" className="text-[10px] uppercase tracking-widest bg-white/5 border-white/10">
                        {mode.badge}
                      </Badge>
                      <span className="text-xs text-muted-foreground">⏱ {mode.time}</span>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-3">{mode.desc}</p>
                    <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {mode.details.map((d, i) => (
                        <li key={i} className="text-xs text-white/60 flex items-start gap-2">
                          <span className="text-purple-400 mt-0.5">✦</span> {d}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Sources */}
      <section className="py-20 border-b border-white/5">
        <div className="max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-4">Veri Kaynakları</h2>
          <p className="text-center text-muted-foreground mb-12 max-w-xl mx-auto">
            Gerçek zamanlı olarak 6+ platformdan sinyal topluyoruz
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {dataSources.map((src, idx) => (
              <div key={idx} className="rounded-xl bg-card border border-white/5 p-5 hover:border-purple-500/20 transition-all group">
                <src.icon className="w-8 h-8 text-purple-400 mb-3 group-hover:scale-110 transition-transform" />
                <h4 className="font-semibold text-white text-sm mb-1">{src.name}</h4>
                <p className="text-xs text-muted-foreground">{src.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 border-b border-white/5 bg-gradient-to-r from-purple-900/5 via-transparent to-violet-900/5">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { value: "6+", label: "Veri Kaynağı" },
              { value: "5", label: "Analiz Modu" },
              { value: "3", label: "AI Ajanı" },
              { value: "50K+", label: "Model Veritabanı" },
            ].map((stat, idx) => (
              <div key={idx}>
                <p className="text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                  {stat.value}
                </p>
                <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-4">Sık Sorulan Sorular</h2>
          <p className="text-center text-muted-foreground mb-12">Merak ettiklerinin cevapları</p>
          <div className="space-y-3">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className="rounded-xl bg-card border border-white/5 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full p-5 flex items-center justify-between text-left hover:bg-white/[0.02] transition-colors"
                >
                  <span className="font-medium text-white text-sm">{faq.q}</span>
                  {openFaq === idx ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  )}
                </button>
                {openFaq === idx && (
                  <div className="px-5 pb-5 text-sm text-muted-foreground leading-relaxed animate-in fade-in duration-200">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="py-16 border-t border-white/5">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-4">Hazır mısın?</h2>
          <p className="text-muted-foreground mb-8">Rakiplerinden önce pazar fırsatını keşfet.</p>
          <Link
            href="/"
            className="px-8 py-4 rounded-full bg-gradient-to-r from-purple-600 to-violet-500 text-white font-semibold text-lg shadow-[0_0_40px_-10px_rgba(168,85,247,0.5)] hover:scale-105 transition-all inline-flex items-center gap-2"
          >
            Ücretsiz Tarama Başlat <ArrowRight className="w-5 h-5" />
          </Link>
          <p className="text-xs text-muted-foreground mt-4">Kredi kartı gerekmez • Günlük limit dahilinde tamamen ücretsiz</p>
        </div>
      </section>
    </div>
  );
}
