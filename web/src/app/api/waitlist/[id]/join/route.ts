import { NextResponse } from 'next/server';
import { WaitlistDB } from '@/lib/waitlist-db';

export async function POST(
    request: Request,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const { email } = await request.json();

        if (!email || !email.includes('@')) {
            return NextResponse.json({ error: 'Invalid email address' }, { status: 400 });
        }

        const success = WaitlistDB.addEmail(id, email);
        if (!success) {
            return NextResponse.json({ error: 'Waitlist not found' }, { status: 404 });
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to join waitlist' }, { status: 500 });
    }
}
