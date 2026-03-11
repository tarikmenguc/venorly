import { WaitlistDB } from '@/lib/waitlist-db';
import { notFound } from 'next/navigation';
import WaitlistClient from './WaitlistClient';

export default async function WaitlistPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const waitlist = WaitlistDB.get(id);

    if (!waitlist) {
        notFound();
    }

    return <WaitlistClient waitlist={waitlist} />;
}
