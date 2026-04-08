import { NextResponse } from 'next/server';
import { ScanDB } from '@/lib/scan-db';
import { supabase } from '@/lib/supabase';

export async function GET() {
    try {
        // Temel istatistikler
        const stats = await ScanDB.getStats();
        const recent = await ScanDB.getRecent(5);

        // Waitlist bilgileri
        let waitlist_count = 0;
        let total_emails = 0;
        try {
            const { data: waitlists, error } = await supabase
                .from('waitlists')
                .select('emails');
            if (!error && waitlists) {
                waitlist_count = waitlists.length;
                total_emails = waitlists.reduce(
                    (sum: number, w: { emails?: string[] }) => sum + (w.emails?.length || 0),
                    0
                );
            }
        } catch (_) { /* waitlist tablosu boşsa sessizce geç */ }

        // İlk tarama tarihi (üye tarihi olarak kullan)
        let member_since: string | null = null;
        try {
            const { data: first } = await supabase
                .from('scans')
                .select('created_at')
                .order('created_at', { ascending: true })
                .limit(1)
                .single();
            member_since = first?.created_at ?? null;
        } catch (_) { /* yeni hesap, tarama yok */ }

        // En çok kullanılan mod
        const modeEntries = Object.entries(stats.modes) as [string, number][];
        const favorite_mode = modeEntries.reduce(
            (best, curr) => (curr[1] > best[1] ? curr : best),
            ['', 0]
        )[0] || null;

        // Top 5 kategori
        let top_categories: { category: string; count: number }[] = [];
        try {
            const { data: scanRows } = await supabase
                .from('scans')
                .select('category')
                .eq('status', 'completed');

            if (scanRows) {
                const counts: Record<string, number> = {};
                for (const row of scanRows) {
                    if (row.category) counts[row.category] = (counts[row.category] || 0) + 1;
                }
                top_categories = Object.entries(counts)
                    .map(([category, count]) => ({ category, count }))
                    .sort((a, b) => b.count - a.count)
                    .slice(0, 5);
            }
        } catch (_) { /* yeni hesap */ }

        return NextResponse.json({
            stats: {
                ...stats,
                waitlist_count,
                total_emails,
            },
            recent_scans: recent,
            member_since,
            favorite_mode,
            top_categories,
        });
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}
