import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { BACKEND_URL, authFetch } from '@/lib/api';
import { useEffect } from "react";

export interface StreakMilestone {
    days_required: number;
    reward_description: string;
    icon_name: string;
    reward_feature?: string | null;
    reward_amount?: number | null;
    completed: boolean;
    claimed?: boolean;
    claimable?: boolean;
}

export interface StreakData {
    type: string;
    timezone: string;
    current_streak: number;
    longest_streak: number;
    last_activity_date: string | null;
    last_action_at: string | null;
    next_milestone: StreakMilestone | null;
    milestones: StreakMilestone[];
    today_complete: boolean;
}

function getTimezone(): string {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
        return "UTC";
    }
}

function getLocalDay(timezone: string): string {
    try {
        return new Intl.DateTimeFormat("en-CA", {
            timeZone: timezone,
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
        }).format(new Date());
    } catch {
        return new Intl.DateTimeFormat("en-CA", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
        }).format(new Date());
    }
}

function getOpenDateKey(uid: string): string {
    return `streak:open:last_date:${uid}`;
}

function getOpenTzKey(uid: string): string {
    return `streak:open:tz:${uid}`;
}

async function fetchStreak(type: string): Promise<StreakData | null> {
    if (!auth) return null;
    const user = auth.currentUser;
    if (!user) return null;

    const res = await authFetch(`${BACKEND_URL}/v1/streak?type=${encodeURIComponent(type)}`);

    if (!res.ok) {
        throw new Error("Failed to fetch streak data");
    }

    return res.json();
}

async function recordAppOpen(): Promise<{ success: boolean; current_streak: number }> {
    if (!auth) throw new Error("Auth not initialized");
    const user = auth.currentUser;
    if (!user) throw new Error("User not authenticated");

    const timezone = getTimezone();
    const res = await authFetch(`${BACKEND_URL}/v1/streak/open?timezone=${encodeURIComponent(timezone)}`, {
        method: "POST",
    });

    if (!res.ok) {
        throw new Error("Failed to record app open");
    }

    return res.json();
}

async function claimReward(type: string, daysRequired: number): Promise<{
    claimed: boolean;
    reward?: { feature: string; amount: number; days_required: number };
    balance?: number;
    reason?: string;
}> {
    if (!auth) throw new Error("Auth not initialized");
    const user = auth.currentUser;
    if (!user) throw new Error("User not authenticated");

    const res = await authFetch(`${BACKEND_URL}/v1/streak/claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, days_required: daysRequired }),
    });

    if (!res.ok) {
        throw new Error("Failed to claim reward");
    }

    return res.json();
}

type UseStreakOptions = {
    type?: string;
    enableOpenTracking?: boolean;
};

export function useStreak(options: UseStreakOptions = {}) {
    const { type = "open", enableOpenTracking = type === "open" } = options;
    const queryClient = useQueryClient();

    const streakQuery = useQuery({
        queryKey: ["userStreak", type],
        queryFn: () => fetchStreak(type),
        enabled: !!auth?.currentUser,
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: true,
    });

    const recordOpenMutation = useMutation({
        mutationFn: recordAppOpen,
        onSuccess: () => {
            const uid = auth?.currentUser?.uid;
            if (uid) {
                const timezone = getTimezone();
                const today = getLocalDay(timezone);
                try {
                    sessionStorage.setItem(getOpenDateKey(uid), today);
                    sessionStorage.setItem(getOpenTzKey(uid), timezone);
                } catch {
                    // Ignore storage errors in restricted environments
                }
            }
            // Invalidate streak query to refresh data
            queryClient.invalidateQueries({ queryKey: ["userStreak", "open"] });
        },
    });

    const claimRewardMutation = useMutation({
        mutationFn: ({ type, daysRequired }: { type: string; daysRequired: number }) =>
            claimReward(type, daysRequired),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["userStreak"] });
            queryClient.invalidateQueries({ queryKey: ["userMe"] });
        },
    });

    // Record app open on initial mount
    useEffect(() => {
        const user = auth?.currentUser;
        if (!user || recordOpenMutation.isPending || recordOpenMutation.isSuccess) return;
        if (!enableOpenTracking) return;

        const timezone = getTimezone();
        const today = getLocalDay(timezone);
        const uid = user.uid;
        let shouldRecord = true;

        try {
            const lastDate = sessionStorage.getItem(getOpenDateKey(uid));
            const lastTz = sessionStorage.getItem(getOpenTzKey(uid));
            shouldRecord = lastDate !== today || lastTz !== timezone;
        } catch {
            shouldRecord = true;
        }

        if (shouldRecord) {
            recordOpenMutation.mutate();
        }
    }, [auth?.currentUser?.uid, recordOpenMutation.isPending, recordOpenMutation.isSuccess, enableOpenTracking]);

    return {
        streak: streakQuery.data,
        isLoading: streakQuery.isLoading,
        isError: streakQuery.isError,
        error: streakQuery.error,
        refetch: streakQuery.refetch,
        claimReward: claimRewardMutation.mutateAsync,
        isClaiming: claimRewardMutation.isPending,
        claimError: claimRewardMutation.error,
    };
}
