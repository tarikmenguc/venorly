import { NextResponse } from 'next/server';
import Stripe from 'stripe';

// Stripe secret key initialization
const stripeKey = process.env.STRIPE_SECRET_KEY;
if (!stripeKey) {
    console.warn("STRIPE_SECRET_KEY not configured - payment disabled");
}
const stripe = stripeKey ? new Stripe(stripeKey, {
    apiVersion: '2023-10-16' as any // Type assertion for compatibility if needed
}) : null;

export async function POST(request: Request) {
    try {
        if (!stripe) {
            return NextResponse.json({ error: 'Payment system not configured' }, { status: 503 });
        }

        const body = await request.json();
        const { planId, planName, price } = body;

        if (!planId) {
            return NextResponse.json({ error: 'Plan ID is required' }, { status: 400 });
        }

        // Fiyatı string'den (örn: "$29") number'a (örn: 29) çevir
        const priceAmount = parseInt(price.replace(/[^0-9]/g, '')) * 100; // Stripe cent olarak çalışır

        if (priceAmount === 0) {
             return NextResponse.json({ error: 'Free plan does not require checkout' }, { status: 400 });
        }

        const origin = request.headers.get('origin') || 'http://localhost:3000';

        // Create Checkout Sessions from body params.
        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card'],
            line_items: [
                {
                    price_data: {
                        currency: 'usd',
                        product_data: {
                            name: `Startup Idea Finder - ${planName} Plan`,
                            description: 'Friction Economy Engine pazar istihbaratı erişimi.',
                        },
                        unit_amount: priceAmount,
                    },
                    quantity: 1,
                },
            ],
            mode: 'payment', // veya abonelik için 'subscription'
            success_url: `${origin}/dashboard?session_id={CHECKOUT_SESSION_ID}&payment=success`,
            cancel_url: `${origin}/pricing?payment=cancelled`,
        });

        return NextResponse.json({ url: session.url });
    } catch (error) {
        console.error("Stripe error:", error);
        return NextResponse.json({ error: String(error) }, { status: 500 });
    }
}
