"use client";

// Skip prerendering
export const dynamic = 'force-dynamic';

import { Suspense, useEffect, useState } from "react";
import { auth } from "@/lib/firebaseClient";
import { authFetch, BACKEND_URL } from "@/lib/api";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Loader2, Activity } from "lucide-react";

interface UsageItem {
    feature: string;
    period: string;
    limit: number | null;
    used: number;
}

function BillingReturnContent() {
    const [usage, setUsage] = useState<UsageItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;

        const fetchUsage = async () => {
            if (!auth.currentUser) {
                // Wait a bit for auth to init
                return;
            }

            try {
                const res = await authFetch(`${BACKEND_URL}/v1/user/me`);
                if (!res.ok) {
                    throw new Error("Failed to load usage data");
                }
                const data = await res.json();
                if (active) {
                    setUsage(data.usage || []);
                    setLoading(false);
                }
            } catch (err: any) {
                console.error("Error fetching usage:", err);
                if (active) {
                    setError(err.message);
                    setLoading(false);
                }
            }
        };

        // Auth listener to trigger fetch when user is ready
        const unsubscribe = auth.onAuthStateChanged((user) => {
            if (user) {
                fetchUsage();
            } else {
                setLoading(false); // No user, stop loading
            }
        });

        return () => {
            active = false;
            unsubscribe();
        };
    }, []);

    if (loading) {
        return (
            <div className="container mx-auto py-20 px-4 text-center flex flex-col items-center justify-center min-h-[50vh]">
                <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
                <h2 className="text-2xl font-bold">Loading Usage Stats...</h2>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto py-20 px-4 text-center">
                <h2 className="text-xl font-bold text-red-500">Error</h2>
                <p className="text-muted-foreground mt-2">{error}</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-10 px-4">
            <div className="mb-8 text-center">
                <h1 className="text-3xl font-bold tracking-tight">Usage Statistics</h1>
                <p className="text-muted-foreground mt-2">
                    Track your resource consumption.
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 lg:max-w-4xl lg:mx-auto">
                {usage.map((item, index) => (
                    <Card key={index} className="bg-card border-border/50">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                                <Activity className="h-4 w-4" />
                                {formatFeatureName(item.feature)}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-baseline gap-1 mt-1">
                                <span className="text-3xl font-bold">{item.used}</span>
                                <span className="text-sm text-muted-foreground">
                                    {item.limit && item.limit < 999999
                                        ? `/ ${item.limit}`
                                        : " used"}
                                </span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-3 capitalize">
                                {item.period} period
                            </p>
                        </CardContent>
                    </Card>
                ))}

                {usage.length === 0 && (
                    <div className="col-span-full text-center text-muted-foreground py-10">
                        No usage recorded yet.
                    </div>
                )}
            </div>
        </div>
    );
}

function formatFeatureName(feature: string): string {
    return feature.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function BillingReturnPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <BillingReturnContent />
        </Suspense>
    );
}
