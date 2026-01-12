import { useQuery } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { BACKEND_URL, authFetch } from '@/lib/api';
import { useEffect, useState } from "react";

export interface UserUsage {
    feature: string;
    period: string;
    limit: number;
    used: number;
}

export interface PendingDowngrade {
    target_product_id: string;
    target_role: string;
    created_at: string;
}

export interface UserSubscription {
    has_subscription: boolean;
    role: string;
    subscription_id?: string;
    customer_id?: string;
    product_id?: string;
    status?: string;  // active, on_hold, cancelled, expired
    cancel_at_period_end?: boolean;
    current_period_start?: string;
    current_period_end?: string;
    pending_downgrade?: PendingDowngrade;
}

export interface UserProfile {
    id: string | null;
    firebase_uid: string;
    email: string | null;
    role: string;
    usage: UserUsage[];
    credits?: {
        total: number;
        used: number;
        remaining: number;
    };
    period_start?: string;
    next_reset?: string;
}

async function fetchMe(): Promise<UserProfile | null> {
    if (!auth) return null;
    const user = auth.currentUser;
    if (!user) return null;

    const res = await authFetch(`${BACKEND_URL}/v1/user/me`);

    if (!res.ok) {
        throw new Error("Failed to fetch user profile");
    }

    return res.json();
}

async function fetchSubscription(): Promise<UserSubscription | null> {
    if (!auth) return null;
    const user = auth.currentUser;
    if (!user) return null;

    try {
        const res = await authFetch(`${BACKEND_URL}/v1/billing/subscription`);
        if (!res.ok) {
            return { has_subscription: false, role: 'free' };
        }
        return res.json();
    } catch {
        return { has_subscription: false, role: 'free' };
    }
}

export function useUser() {
    const [isAuthReady, setIsAuthReady] = useState(false);

    useEffect(() => {
        if (!auth) return;
        const unsubscribe = auth.onAuthStateChanged(() => {
            setIsAuthReady(true);
        });
        return () => unsubscribe();
    }, []);

    const profileQuery = useQuery({
        queryKey: ["userMe"],
        queryFn: fetchMe,
        enabled: !!auth && isAuthReady && !!auth.currentUser,
        staleTime: 60 * 1000, // 1 minute
    });

    const subscriptionQuery = useQuery({
        queryKey: ["userSubscription"],
        queryFn: fetchSubscription,
        enabled: !!auth && isAuthReady && !!auth.currentUser,
        staleTime: 60 * 1000,
    });

    return {
        ...profileQuery,
        user: auth ? auth.currentUser : null,
        profile: profileQuery.data,
        subscription: subscriptionQuery.data,
        isAuthLoading: !isAuthReady,
        isLoading: profileQuery.isLoading || subscriptionQuery.isLoading,
    };
}

