import { useQuery } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { BACKEND_URL, authFetch } from '@/lib/api';
import { useCallback, useEffect, useState } from "react";

export interface UserUsage {
    feature: string;
    period: string;
    limit: number;
    used: number;
}

export interface BillingSummary {
    billing_state?: string;
    subscription_status?: string;
    payment_status?: string;
    access_status?: string;
    entitlement_status?: string;
    effective_product_id?: string;
    provider_product_id?: string;
    current_period_start?: string;
    current_period_end?: string;
    cancel_at_period_end?: boolean;
    renews_at?: string | null;
    ends_at?: string | null;
    is_trialing?: boolean;
    trial_ends_at?: string | null;
    first_charge_at?: string | null;
    trial_period_days?: number;
    on_hold_reason?: string | null;
}

export interface CurrentBillingOperation {
    id: string;
    type: string;
    status: string;
    ui_status?: string;
    subscription_id?: string | null;
    requested_from_product_id?: string | null;
    requested_to_product_id?: string | null;
    result_product_id?: string | null;
    failure_reason?: string | null;
    metadata?: Record<string, unknown>;
    started_at?: string | null;
    completed_at?: string | null;
}

export interface PaymentIssue {
    payment_id: string;
    status: string;
    amount?: number;
    currency?: string;
    failure_code?: string | null;
    failure_message?: string | null;
    updated_at?: string | null;
}

export interface PendingChange {
    type: string;
    status: string;
    target_product_id?: string | null;
    target_role?: string | null;
    effective_at?: string | null;
    created_at?: string | null;
}

export interface BillingHistoryItem {
    id: string;
    event_name: string;
    subscription_id?: string | null;
    operation_id?: string | null;
    payload?: Record<string, unknown>;
    created_at?: string | null;
}

export interface UserSubscription {
    has_subscription: boolean;
    role: string;
    can_manage_billing?: boolean;
    billing_state?: string;
    allowed_actions?: string[];
    access_granted?: boolean;
    cancelled_with_access?: boolean;
    subscription_id?: string;
    customer_id?: string;
    product_id?: string;
    status?: string;  // active, on_hold, cancelled, expired
    provider_product_id?: string;
    effective_product_id?: string;
    payment_status?: string;
    access_status?: string;
    entitlement_status?: string;
    cancel_at_period_end?: boolean;
    current_period_start?: string;
    current_period_end?: string;
    summary?: BillingSummary;
    current_operation?: CurrentBillingOperation | null;
    payment_issue?: PaymentIssue | null;
    pending_change?: PendingChange | null;
    history?: BillingHistoryItem[];
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
        bonus?: number;
        remaining: number;
    };
    reward_balances?: Record<string, number>;
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

type UseUserOptions = {
    refreshOnMount?: boolean;
};

export function useUser(options: UseUserOptions = {}) {
    const [isAuthReady, setIsAuthReady] = useState(false);
    const { refreshOnMount = false } = options;

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
    const profileRefetch = profileQuery.refetch;
    const subscriptionRefetch = subscriptionQuery.refetch;

    const refreshUser = useCallback(async () => {
        if (!auth?.currentUser) return;
        await auth.currentUser.getIdToken(true);
        await Promise.all([profileRefetch(), subscriptionRefetch()]);
    }, [profileRefetch, subscriptionRefetch]);

    useEffect(() => {
        if (refreshOnMount && isAuthReady && auth?.currentUser) {
            void refreshUser();
        }
    }, [refreshOnMount, isAuthReady, refreshUser]);

    return {
        ...profileQuery,
        user: auth ? auth.currentUser : null,
        profile: profileQuery.data,
        subscription: subscriptionQuery.data,
        isAuthLoading: !isAuthReady,
        isLoading: profileQuery.isLoading || subscriptionQuery.isLoading,
        refreshUser,
    };
}
