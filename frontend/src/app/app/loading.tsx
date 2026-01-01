"use client";

import { Sparkles } from "lucide-react";

export default function AppHomeLoading() {
    return (
        <div className="min-h-screen bg-background relative flex items-center justify-center animate-in fade-in duration-300">
            <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] bg-blue-600/10 rounded-full blur-[160px] animate-pulse" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[70%] bg-primary/10 rounded-full blur-[160px]" />
            </div>
            <div className="flex flex-col items-center gap-3 text-center">
                <div className="h-12 w-12 rounded-full glass flex items-center justify-center">
                    <Sparkles className="h-5 w-5 text-primary animate-pulse" />
                </div>
                <p className="text-sm text-muted-foreground">Loading your workspace…</p>
            </div>
        </div>
    );
}
