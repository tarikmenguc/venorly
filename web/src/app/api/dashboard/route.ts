import { NextResponse } from 'next/server';
import { ScanDB } from '@/lib/scan-db';

export async function GET() {
    try {
        const stats = ScanDB.getStats();
        const recent = ScanDB.getRecent(10);

        // Waitlist verilerini de topla
        let waitlist_count = 0;
        let total_emails = 0;
        try {
            const { WaitlistDB } = await import('@/lib/waitlist-db');
            // WaitlistDB'den tüm waitlist'leri al (getAll metodu yok, 
            // o yüzden tüm dosyayı okuyoruz)
            const fs = await import('fs');
            const path = await import('path');
            const dbPath = path.join(process.cwd(), '.data', 'waitlists.json');
            if (fs.existsSync(dbPath)) {
                const data = JSON.parse(fs.readFileSync(dbPath, 'utf-8'));
                const entries = Object.values(data) as any[];
                waitlist_count = entries.length;
                total_emails = entries.reduce((sum: number, w: any) => sum + (w.emails?.length || 0), 0);
            }
        } catch {
            // Waitlist dosyası yoksa sorun değil
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
