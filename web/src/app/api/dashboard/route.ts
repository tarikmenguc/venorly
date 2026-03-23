import { NextResponse } from 'next/server';
import { ScanDB } from '@/lib/scan-db';
import { supabase } from '@/lib/supabase';

export async function GET() {
    try {
        const stats = await ScanDB.getStats();
        const recent = await ScanDB.getRecent(10);

        let waitlist_count = 0;
        let total_emails = 0;

        try {
            const { data: waitlists, error } = await supabase
                .from('waitlists')
                .select('emails');

            if (!error && waitlists) {
                waitlist_count = waitlists.length;
                total_emails = waitlists.reduce((sum: number, w: { emails?: string[] }) => sum + (w.emails?.length || 0), 0);
            }
        } catch (e) {
            console.error("Waitlist stats error:", e);
        }

        return NextResponse.json({
            stats: {
                ...stats,
                waitlist_count,
                total_emails,
            },
            recent_scans: recent,
        });
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}
