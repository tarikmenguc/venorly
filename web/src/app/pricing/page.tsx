"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Check,
  Zap,
  Crown,
  Building2,
  ArrowLeft,
  Sparkles,
} from "lucide-react";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "aylık",
    description: "Başlangıç için ideal",
    icon: Zap,
    gradient: "from-gray-600 to-gray-400",
    buttonText: "Hemen Başla",
    buttonStyle: "bg-white/5 border border-white/10 hover:bg-white/10 text-white",
    features: [
      "Günde 3 Keşfet taraması",
      "Temel AI fırsat raporu",
      "1 aktif waitlist sayfası",
      "Topluluk desteği",
    ],
    limitations: [
      "Derin Analiz modu yok",
      "Orkestratör modu yok",
      "Lead yönetimi yok",
    ],
  },
  {
    name: "Pro",
    price: "$29",
    period: "aylık",
    description: "Ciddi girişimciler için",
    icon: Crown,
    gradient: "from-purple-600 to-violet-400",
    popular: true,
    buttonText: "Pro'ya Yükselt",
    buttonStyle: "bg-gradient-to-r from-purple-600 to-violet-500 text-white hover:opacity-90 shadow-[0_0_30px_-5px_rgba(139,92,246,0.5)]",
    features: [
      "Sınırsız tarama (tüm modlar)",
      "Derin Analiz + Orkestratör",
      "n8n/Make.com istihbaratı",
      "Product Hunt boşluk analizi",
      "Lead yönetimi + DM şablonları",
      "10 aktif waitlist sayfası",
      "Investment Memo çıktısı",
      "Öncelikli destek",
    ],
    limitations: [],
  },
  {
    name: "Enterprise",
    price: "$99",
    period: "aylık",
    description: "Ajanslar ve ekipler için",
    icon: Building2,
    gradient: "from-amber-500 to-orange-400",
    buttonText: "İletişime Geç",
    buttonStyle: "bg-gradient-to-r from-amber-500 to-orange-400 text-black font-semibold hover:opacity-90",
    features: [
      "Pro'daki her şey +",
      "Sınırsız waitlist sayfası",
      "PDF rapor dışa aktarma",
      "API erişimi",
      "Niş Alarm sistemi",
      "Özel AI model eğitimi",
      "Çoklu kullanıcı desteği",
      "Dedicated müşteri temsilcisi",
    ],
    limitations: [],
  },
];

export default function PricingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-white/5 bg-gradient-to-r from-background via-purple-950/10 to-background">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.push("/dashboard")}
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Dashboard
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-16 space-y-12">
        {/* Title */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium">
            <Sparkles className="w-4 h-4" /> Lansmana Özel Tamamen Ücretsiz
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-white to-white/50 bg-clip-text text-transparent">
            Şimdilik kredi kartına gerek yok
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Ürünümüz şu an erken erişim (Beta) aşamasında olduğu için tüm özellikler geçici bir süreliğine ücretsizdir. Sadece kötüye kullanımı engellemek için günlük IP güvenlik limitleri uygulanmaktadır.
          </p>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border p-6 flex flex-col transition-all hover:scale-[1.02] ${
                plan.popular
                  ? "bg-gradient-to-b from-purple-950/30 to-card border-purple-500/30 shadow-[0_0_60px_-15px_rgba(139,92,246,0.3)]"
                  : "bg-card border-white/5 hover:border-white/10"
              }`}
            >
              {/* Popular badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-purple-600 to-violet-500 text-white text-xs font-semibold">
                  ⚡ En Popüler
                </div>
              )}

              {/* Plan header */}
              <div className="mb-6">
                <div className={`inline-flex p-2.5 rounded-xl bg-gradient-to-br ${plan.gradient} mb-4`}>
                  <plan.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{plan.description}</p>
              </div>

              {/* Price */}
              <div className="mb-6">
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-extrabold text-white">{plan.price}</span>
                  <span className="text-sm text-muted-foreground">/{plan.period}</span>
                </div>
              </div>

              {/* CTA Button */}
              <button
                onClick={() => router.push("/dashboard")}
                className={`w-full py-3 rounded-xl text-sm font-semibold transition-all mb-6 flex items-center justify-center ${plan.buttonStyle}`}
              >
                {plan.buttonText}
              </button>

              {/* Features */}
              <div className="flex-1 space-y-3">
                {plan.features.map((feature, i) => (
                  <div key={i} className="flex items-start gap-2.5">
                    <Check className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                    <span className="text-sm text-muted-foreground">{feature}</span>
                  </div>
                ))}

                {plan.limitations.map((lim, i) => (
                  <div key={i} className="flex items-start gap-2.5 opacity-40">
                    <span className="w-4 h-4 shrink-0 mt-0.5 text-center text-xs text-muted-foreground">✗</span>
                    <span className="text-sm text-muted-foreground line-through">{lim}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* FAQ or Trust signals */}
        <div className="text-center space-y-4 pt-8">
          <p className="text-sm text-muted-foreground">
            Tüm planlar 14 gün ücretsiz deneme içerir. Kredi kartı gerekmez.
          </p>
          <p className="text-xs text-muted-foreground">
            Ödemeler Stripe ile güvenli şekilde işlenir 🔒
          </p>
        </div>

        {/* Footer */}
        <div className="text-center py-6">
          <p className="text-xs text-muted-foreground">
            Venorly
          </p>
        </div>
      </div>
    </div>
  );
}
