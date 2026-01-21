"use client";

import Image from "next/image";

export default function AppHomeLoading() {
    return (
        <div className="min-h-screen bg-background flex items-center justify-center">
            <div className="relative">
                {/* Spinner ring */}
                <div
                    className="absolute rounded-full border-2 border-transparent border-t-white animate-spin"
                    style={{
                        width: '72px',
                        height: '72px',
                        top: '-4px',
                        left: '-4px',
                    }}
                />
                {/* Logo */}
                <div className="h-16 w-16 rounded-full overflow-hidden bg-white/5 flex items-center justify-center">
                    <Image
                        src="/images/image.png"
                        alt="Logo"
                        width={54}
                        height={54}
                        priority
                        className="object-contain"
                    />
                </div>
            </div>
        </div>
    );
}
