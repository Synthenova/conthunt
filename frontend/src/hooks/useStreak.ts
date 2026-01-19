import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { BACKEND_URL, authFetch } from '@/lib/api';
import { useEffect } from "react";

export interface StreakMilestone {
    days_required: number;
    reward_description: string;
    icon_name: string;
    completed: boolean;
}

export interface StreakData {
    current_streak: number;
    longest_streak: number;
    last_activity_date: string | null;
    next_milestone: StreakMilestone | null;
    milestones: StreakMilestone[];
    today_complete: boolean;
    today_status: {
        app_opened: boolean;
        search_done: boolean;
    };
}

function getTimezone(): string {
    try {
        return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch {
        return "UTC";
    }
}

async function fetchStreak(): Promise<StreakData | null> {
    if (!auth) return null;
    const user = auth.currentUser;
    if (!user) return null;

    const timezone = getTimezone();
    const res = await authFetch(`${BACKEND_URL}/v1/streak?timezone=${encodeURIComponent(timezone)}`);

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

export function useStreak() {
    const queryClient = useQueryClient();

    const streakQuery = useQuery({
        queryKey: ["userStreak"],
        queryFn: fetchStreak,
        enabled: !!auth?.currentUser,
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: true,
    });

    const recordOpenMutation = useMutation({
        mutationFn: recordAppOpen,
        onSuccess: () => {
            // Invalidate streak query to refresh data
            queryClient.invalidateQueries({ queryKey: ["userStreak"] });
        },
    });

    // Record app open on initial mount
    useEffect(() => {
        if (auth?.currentUser && !recordOpenMutation.isPending && !recordOpenMutation.isSuccess) {
            recordOpenMutation.mutate();
        }
    }, [auth?.currentUser]);

    return {
        streak: streakQuery.data,
        isLoading: streakQuery.isLoading,
        isError: streakQuery.isError,
        error: streakQuery.error,
        refetch: streakQuery.refetch,
    };
}
