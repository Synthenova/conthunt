"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { GlassCard } from "@/components/ui/glass-card";

export function BoardCardSkeleton() {
    return (
        <div className="h-64 flex flex-col rounded-2xl border border-white/5 bg-[#0D1118]/50 overflow-hidden">
            <Skeleton className="h-40 w-full" />
            <div className="p-4 flex-1 space-y-3">
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
            </div>
        </div>
    );
}

export function VideoGridSkeleton() {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {[...Array(10)].map((_, i) => (
                <div key={i} className="aspect-[9/16] rounded-xl overflow-hidden">
                    <Skeleton className="h-full w-full" />
                </div>
            ))}
        </div>
    );
}

export function InsightSkeleton() {
    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <Skeleton className="h-8 w-40" />
                <Skeleton className="h-10 w-44" />
            </div>
            <div className="grid md:grid-cols-2 gap-6">
                {[...Array(2)].map((_, i) => (
                    <GlassCard key={i} className="p-6 space-y-4">
                        <Skeleton className="h-6 w-32" />
                        <Skeleton className="h-20 w-full" />
                        <Skeleton className="h-20 w-full" />
                    </GlassCard>
                ))}
            </div>
        </div>
    );
}
