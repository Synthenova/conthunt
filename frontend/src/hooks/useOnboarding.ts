/**
 * Onboarding Tutorial Hook
 * Manages tutorial flow status and progression via React Query.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { BACKEND_URL, authFetch } from "@/lib/api";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface FlowStep {
    id: string;
    title: string;
    content: string;
    cta?: { label: string; href: string };
}

export interface FlowSummary {
    id: string;
    name: string;
    page: string;
    total_steps: number;
}

export interface FlowDetail {
    id: string;
    name: string;
    page: string;
    total_steps: number;
    steps: FlowStep[];
}

export interface ProgressStatus {
    flow_id: string;
    status: "not_started" | "in_progress" | "completed" | "skipped";
    current_step: number;
    total_steps: number;
    restart_count: number;
}

export interface FlowWithProgress {
    flow: FlowDetail;
    progress: ProgressStatus;
}

// ─────────────────────────────────────────────────────────────────────────────
// API Functions
// ─────────────────────────────────────────────────────────────────────────────

async function fetchAllFlows(): Promise<FlowSummary[]> {
    if (!auth?.currentUser) throw new Error("Not authenticated");
    const res = await authFetch(`${BACKEND_URL}/v1/onboarding/flows`);
    if (!res.ok) throw new Error("Failed to fetch flows");
    return res.json();
}

async function fetchAllStatus(): Promise<ProgressStatus[]> {
    if (!auth?.currentUser) throw new Error("Not authenticated");
    const res = await authFetch(`${BACKEND_URL}/v1/onboarding/status`);
    if (!res.ok) throw new Error("Failed to fetch status");
    return res.json();
}

async function fetchFlowStatus(flowId: string): Promise<FlowWithProgress> {
    if (!auth?.currentUser) throw new Error("Not authenticated");
    const res = await authFetch(`${BACKEND_URL}/v1/onboarding/status/${flowId}`);
    if (!res.ok) throw new Error("Failed to fetch flow status");
    return res.json();
}

async function startFlow(flowId: string, replay: boolean = false): Promise<ProgressStatus> {
    if (!auth?.currentUser) throw new Error("Not authenticated");
    const res = await authFetch(`${BACKEND_URL}/v1/onboarding/start`, {
        method: "POST",
        body: JSON.stringify({ flow_id: flowId, replay }),
    });
    if (!res.ok) throw new Error("Failed to start flow");
    return res.json();
}

async function completeStep(flowId: string): Promise<ProgressStatus> {
    if (!auth?.currentUser) throw new Error("Not authenticated");
    const res = await authFetch(`${BACKEND_URL}/v1/onboarding/step`, {
        method: "POST",
        body: JSON.stringify({ flow_id: flowId }),
    });
    if (!res.ok) throw new Error("Failed to complete step");
    return res.json();
}

async function skipFlow(flowId: string): Promise<ProgressStatus> {
    if (!auth?.currentUser) throw new Error("Not authenticated");
    const res = await authFetch(`${BACKEND_URL}/v1/onboarding/skip`, {
        method: "POST",
        body: JSON.stringify({ flow_id: flowId }),
    });
    if (!res.ok) throw new Error("Failed to skip flow");
    return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Hook to get all available flows (for profile dropdown).
 */
export function useOnboardingFlows() {
    return useQuery({
        queryKey: ["onboarding", "flows"],
        queryFn: fetchAllFlows,
        enabled: !!auth?.currentUser,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

/**
 * Hook to get status of all flows for current user.
 */
export function useAllOnboardingStatus() {
    return useQuery({
        queryKey: ["onboarding", "status", "all"],
        queryFn: fetchAllStatus,
        enabled: !!auth?.currentUser,
        staleTime: 30 * 1000, // 30 seconds
    });
}

/**
 * Hook to get status and details for a specific flow.
 */
export function useOnboardingStatus(flowId: string) {
    return useQuery({
        queryKey: ["onboarding", "status", flowId],
        queryFn: () => fetchFlowStatus(flowId),
        enabled: !!auth?.currentUser && !!flowId,
        staleTime: 30 * 1000,
    });
}

/**
 * Hook for flow mutations (start, complete step, skip).
 */
export function useOnboardingActions() {
    const queryClient = useQueryClient();

    const invalidateQueries = () => {
        queryClient.invalidateQueries({ queryKey: ["onboarding"] });
    };

    const startMutation = useMutation({
        mutationFn: ({ flowId, replay }: { flowId: string; replay?: boolean }) =>
            startFlow(flowId, replay || false),
        onSuccess: invalidateQueries,
    });

    const completeMutation = useMutation({
        mutationFn: (flowId: string) => completeStep(flowId),
        onSuccess: invalidateQueries,
    });

    const skipMutation = useMutation({
        mutationFn: (flowId: string) => skipFlow(flowId),
        onSuccess: invalidateQueries,
    });

    return {
        startFlow: startMutation.mutateAsync,
        completeStep: completeMutation.mutateAsync,
        skipFlow: skipMutation.mutateAsync,
        isStarting: startMutation.isPending,
        isCompleting: completeMutation.isPending,
        isSkipping: skipMutation.isPending,
    };
}
