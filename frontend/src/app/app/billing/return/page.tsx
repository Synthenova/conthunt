"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { auth } from "@/lib/firebaseClient";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Check } from "lucide-react";
import { toast } from "sonner";

function BillingReturnContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [loading, setLoading] = useState<string | null>(null);
    const [role, setRole] = useState<string | null>(null);

    const status = searchParams.get("status");
    const subscriptionId = searchParams.get("subscription_id");

    useEffect(() => {
        // Listen for auth changes to get the latest role (claims)
        const unsubscribe = auth.onIdTokenChanged(async (user) => {
            if (user) {
                // Force refresh token if status just changed to active to ensure claims are up to date?
                // For now, just get result. If webhook was fast, claim might be updated.
                // If status is 'active', we might want to force refresh?
                const forceRefresh = status === "active";
                const token = await user.getIdTokenResult(forceRefresh);
                setRole((token.claims.role as string) || "free");
            } else {
                setRole(null);
            }
        });
        return () => unsubscribe();
    }, [status]); // Run when status changes too, in case of redirect update

    useEffect(() => {
        if (status === "active") {
            toast.success("Subscription activated successfully!", {
                description: `ID: ${subscriptionId}`,
                duration: 5000,
            });
        } else if (status === "failed") {
            toast.error("Subscription payment failed.", {
                description: "Stayed on previous plan. Please try again.",
                duration: 5000,
            });
        } else if (status === "cancelled") {
            toast.info("Subscription setup cancelled.");
        }
    }, [status, subscriptionId]);

    const handleSubscribe = async (plan: "creator" | "pro_research") => {
        try {
            setLoading(plan);
            const user = auth.currentUser;
            if (!user) {
                toast.error("Please log in to subscribe.");
                return;
            }

            const idToken = await user.getIdToken();
            const res = await fetch("http://localhost:8000/v1/billing/dodo/checkout-session", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${idToken}`,
                },
                body: JSON.stringify({ plan }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to start checkout");
            }

            const data = await res.json();
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                throw new Error("No checkout URL returned");
            }
        } catch (error: any) {
            toast.error(error.message);
        } finally {
            setLoading(null);
        }
    };

    const isPlanActive = (planRole: string) => role === planRole;

    return (
        <div className="container mx-auto py-10 px-4">
            <div className="mb-8 text-center">
                <h1 className="text-3xl font-bold tracking-tight">Manage Subscription</h1>
                <p className="text-muted-foreground mt-2">
                    {status === "failed"
                        ? "Your last payment failed. Please choose a plan to retry."
                        : "Choose the plan that powers your research."}
                </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:max-w-4xl lg:mx-auto">
                {/* Creator Plan */}
                <Card className={`flex flex-col border-border/50 bg-black text-white relative overflow-hidden ${isPlanActive("creator") ? "border-green-500/50" : ""}`}>
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        {/* Decorative Background Element */}
                    </div>
                    <CardHeader>
                        <CardTitle className="text-muted-foreground text-sm font-medium uppercase tracking-wider">Creator</CardTitle>
                        <div className="flex items-baseline gap-1 mt-2">
                            <span className="text-4xl font-bold">$29</span>
                            <span className="text-muted-foreground">/mo</span>
                        </div>
                    </CardHeader>
                    <CardContent className="flex-1">
                        <ul className="space-y-4 text-sm mt-4">
                            <li className="flex items-center gap-3">
                                <Check className="h-4 w-4 text-primary" />
                                <span>2 Platforms</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <Check className="h-4 w-4 text-primary" />
                                <span>50 AI Analyses / mo</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <Check className="h-4 w-4 text-primary" />
                                <span>Basic Trends</span>
                            </li>
                        </ul>
                    </CardContent>
                    <CardFooter>
                        <Button
                            variant={isPlanActive("creator") ? "secondary" : "outline"}
                            className={`w-full ${isPlanActive("creator") ? "bg-green-600 hover:bg-green-700 text-white" : "bg-transparent border-white/20 hover:bg-white/10 text-white"}`}
                            onClick={() => handleSubscribe("creator")}
                            disabled={!!loading || isPlanActive("creator")}
                        >
                            {loading === "creator" ? "Processing..." : isPlanActive("creator") ? "Current Plan" : "Subscribe"}
                        </Button>
                    </CardFooter>
                </Card>

                {/* Pro Research Plan */}
                <Card className={`flex flex-col border-primary/50 bg-black text-white relative shadow-lg shadow-primary/10 ${isPlanActive("pro_research") ? "border-green-500/50" : ""}`}>
                    <div className="absolute top-0 right-0 bg-primary px-3 py-1 rounded-bl-lg text-xs font-semibold text-primary-foreground">
                        MOST POPULAR
                    </div>
                    <CardHeader>
                        <CardTitle className="text-primary text-sm font-medium uppercase tracking-wider">Pro Research</CardTitle>
                        <div className="flex items-baseline gap-1 mt-2">
                            <span className="text-4xl font-bold">$79</span>
                            <span className="text-muted-foreground">/mo</span>
                        </div>
                    </CardHeader>
                    <CardContent className="flex-1">
                        <ul className="space-y-4 text-sm mt-4">
                            <li className="flex items-center gap-3">
                                <Check className="h-4 w-4 text-primary" />
                                <span>All Platforms</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <Check className="h-4 w-4 text-primary" />
                                <span>Unlimited AI Analysis</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <Check className="h-4 w-4 text-primary" />
                                <span>Deep Frame Breakdown</span>
                            </li>
                            <li className="flex items-center gap-3">
                                <Check className="h-4 w-4 text-primary" />
                                <span>Export to Notion/CSV</span>
                            </li>
                        </ul>
                    </CardContent>
                    <CardFooter>
                        <Button
                            className={`w-full ${isPlanActive("pro_research") ? "bg-green-600 hover:bg-green-700 text-white" : "bg-white text-black hover:bg-white/90"}`}
                            onClick={() => handleSubscribe("pro_research")}
                            disabled={!!loading || isPlanActive("pro_research")}
                        >
                            {loading === "pro_research" ? "Processing..." : isPlanActive("pro_research") ? "Current Plan" : "Subscribe"}
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
}

export default function BillingReturnPage() {
    return (
        <Suspense fallback={<div>Loading subscription details...</div>}>
            <BillingReturnContent />
        </Suspense>
    );
}
