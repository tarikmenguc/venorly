'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Rocket, CheckCircle2, ChevronRight, XCircle } from 'lucide-react';
import { Waitlist } from '@/lib/waitlist-db';
import { GradientDots } from '@/components/ui/gradient-dots';

export default function WaitlistClient({ waitlist }: { waitlist: Waitlist }) {
    const [email, setEmail] = useState('');
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        setStatus('loading');

        try {
            const res = await fetch(`/api/waitlist/${waitlist.id}/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });

            const data = await res.json();

            if (res.ok && data.success) {
                setStatus('success');
            } else {
                setStatus('error');
                setErrorMessage(data.error || 'Bir hata oluştu. Tekrar deneyin.');
            }
        } catch (err) {
            setStatus('error');
            setErrorMessage('Bağlantı hatası.');
        }
    };

    return (
        <main className="relative min-h-screen bg-black text-white flex flex-col items-center justify-center p-4 overflow-hidden">
            {/* Background */}
            <div className="absolute inset-0 z-0 opacity-40 mix-blend-screen pointer-events-none">
                <GradientDots />
            </div>

            <div className="z-10 w-full max-w-3xl flex flex-col items-center text-center space-y-8 p-8 rounded-3xl bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl">
                <div className="p-4 rounded-full bg-white/10 border border-white/20 mb-4 animate-pulse">
                    <Rocket className="w-10 h-10 text-emerald-400" />
                </div>

                <div className="space-y-4">
                    <div className="inline-block px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-semibold tracking-wide uppercase mb-2">
                        Özel Erişim: {waitlist.target_audience}
                    </div>
                    <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-white to-gray-400 leading-tight">
                        {waitlist.title}
                    </h1>
                    <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed mt-6">
                        {waitlist.description}
                    </p>
                </div>

                <div className="w-full max-w-md mt-10">
                    {status === 'success' ? (
                        <div className="flex flex-col items-center space-y-3 p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                            <CheckCircle2 className="w-10 h-10 text-emerald-400" />
                            <h3 className="text-xl font-bold text-white">İçeridesin!</h3>
                            <p className="text-gray-400 text-sm">Erken erişim açıldığında sana haber vereceğiz.</p>
                        </div>
                    ) : (
                        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
                            <Input
                                type="email"
                                placeholder="E-posta adresin..."
                                value={email}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                    setEmail(e.target.value);
                                    setStatus('idle');
                                }}
                                disabled={status === 'loading'}
                                className="h-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 focus-visible:ring-emerald-500"
                                required
                            />
                            <Button
                                type="submit"
                                disabled={status === 'loading'}
                                className="h-12 px-8 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold transition-all group"
                            >
                                {status === 'loading' ? 'Katılınıyor...' : 'Erken Erişim'}
                                <ChevronRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </Button>
                        </form>
                    )}

                    {status === 'error' && (
                        <div className="flex items-center justify-center space-x-2 mt-4 text-red-400 text-sm bg-red-500/10 py-2 rounded-lg border border-red-500/20">
                            <XCircle className="w-4 h-4" />
                            <span>{errorMessage}</span>
                        </div>
                    )}
                </div>

                <div className="mt-12 text-sm text-gray-500">
                    Spam yok. Sadece ürün hazır olduğunda mail atacağız.
                </div>
            </div>

            {/* Brand footer */}
            <div className="absolute bottom-6 left-0 right-0 text-center z-10">
                <p className="text-xs text-gray-600 font-medium tracking-wider">
                    TESTED WITH <span className="text-gray-400 font-bold">STARTUP FINDER AI</span>
                </p>
            </div>
        </main>
    );
}
