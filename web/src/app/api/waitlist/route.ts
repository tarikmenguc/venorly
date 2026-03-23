import { NextResponse } from 'next/server';
import { WaitlistDB } from '@/lib/waitlist-db';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { title, description, target_audience } = body;

        if (!title || !description) {
            return NextResponse.json({ error: 'Title and description are required' }, { status: 400 });
        }

        const waitlist = await WaitlistDB.create(title, description, target_audience || 'Everyone');
        return NextResponse.json(waitlist);
    } catch (error) {
        return NextResponse.json({ error: 'Failed to create waitlist page' }, { status: 500 });
    }
}
