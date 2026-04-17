import { NextResponse } from 'next/server';
import { AlertDB } from '@/lib/alert-db';

export async function GET() {
    try {
        const alerts = await AlertDB.getAll();
        return NextResponse.json({ alerts });
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { keyword, email, frequency } = body;

        if (!keyword || !email) {
            return NextResponse.json({ error: 'Keyword and email are required' }, { status: 400 });
        }

        const alert = await AlertDB.create(keyword, email, ['reddit', 'github', 'huggingface'], frequency);
        if (!alert) {
             return NextResponse.json({ error: 'Could not create alert' }, { status: 500 });
        }

        return NextResponse.json(alert);
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}

export async function PATCH(request: Request) {
    try {
        const body = await request.json();
        const { id, is_active } = body;

        if (!id || is_active === undefined) {
            return NextResponse.json({ error: 'ID and is_active are required' }, { status: 400 });
        }

        const success = await AlertDB.toggleStatus(id, is_active);
        return NextResponse.json({ success });
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}

export async function DELETE(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const id = searchParams.get('id');

        if (!id) {
            return NextResponse.json({ error: 'ID is required' }, { status: 400 });
        }

        const success = await AlertDB.delete(id);
        return NextResponse.json({ success });
    } catch (error) {
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}
