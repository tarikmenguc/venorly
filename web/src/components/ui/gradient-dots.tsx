"use client";

import React from 'react';

type GradientDotsProps = React.HTMLAttributes<HTMLDivElement> & {
    /** Dot size (default: 1) */
    dotSize?: number;
    /** Spacing between dots (default: 24) */
    spacing?: number;
    /** Opacity (default: 0.3) */
    opacity?: number;
};

/**
 * Lightweight CSS-only dot grid background.
 * No framer-motion, no requestAnimationFrame — zero CPU/GPU overhead.
 */
export function GradientDots({
    dotSize = 1,
    spacing = 24,
    opacity = 0.3,
    className,
    style,
    ...props
}: GradientDotsProps) {
    return (
        <div
            className={`absolute inset-0 ${className || ''}`}
            style={{
                opacity,
                backgroundImage: `
                    radial-gradient(circle, rgba(139,92,246,0.4) ${dotSize}px, transparent ${dotSize}px),
                    radial-gradient(circle at 30% 20%, rgba(139,92,246,0.08) 0%, transparent 50%),
                    radial-gradient(circle at 70% 80%, rgba(59,130,246,0.06) 0%, transparent 50%)
                `,
                backgroundSize: `${spacing}px ${spacing}px, 100% 100%, 100% 100%`,
                backgroundPosition: '0 0, 0 0, 0 0',
                ...style,
            }}
            {...props}
        />
    );
}
