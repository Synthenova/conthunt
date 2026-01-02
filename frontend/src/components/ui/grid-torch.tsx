"use client";

import { useEffect, useRef } from "react";

export function GridTorch() {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!containerRef.current) return;
            // Global coordinates for the fixed grid
            const x = e.clientX;
            const y = e.clientY;
            containerRef.current.style.setProperty("--mouse-x", `${x}px`);
            containerRef.current.style.setProperty("--mouse-y", `${y}px`);
        };

        window.addEventListener("mousemove", handleMouseMove);
        return () => window.removeEventListener("mousemove", handleMouseMove);
    }, []);

    return (
        <div
            ref={containerRef}
            id="grid-torch"
            className="fixed inset-0 z-[-1] pointer-events-none"
        />
    );
}
