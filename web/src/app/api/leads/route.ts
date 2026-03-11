import { NextResponse } from 'next/server';
import { LeadDB } from '@/lib/lead-db';

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const status = searchParams.get('status') as any;

        const leads = status ? LeadDB.getByStatus(status) : LeadDB.getAll();
        const stats = LeadDB.getStats();

        return NextResponse.json({ leads, stats });
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}

export async function PATCH(request: Request) {
    try {
        const body = await request.json();
        const { id, status } = body;

        if (!id || !status) {
            return NextResponse.json({ error: 'id ve status gerekli' }, { status: 400 });
        }

        const success = LeadDB.updateStatus(id, status);
        return NextResponse.json({ success });
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}
