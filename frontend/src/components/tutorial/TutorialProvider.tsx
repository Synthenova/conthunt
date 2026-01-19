/**
 * Tutorial Provider Context
 * Manages active tutorial flow state across the app.
 */
"use client";

import React, {
    createContext,
    useContext,
    useState,
    useCallback,
    useEffect,
    useMemo,
} from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import {
    useOnboardingStatus,
    useOnboardingActions,
    FlowWithProgress,
    FlowStep,
} from "@/hooks/useOnboarding";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

interface TutorialContextValue {
    // State
    isActive: boolean;
    flowId: string | null;
    currentStep: FlowStep | null;
    stepIndex: number;
    totalSteps: number;
    progress: FlowWithProgress | null;

    // Actions
    startFlow: (flowId: string, replay?: boolean) => Promise<void>;
    nextStep: () => Promise<void>;
    skipFlow: () => Promise<void>;
    closeTutorial: () => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────

const TutorialContext = createContext<TutorialContextValue | null>(null);

export function useTutorial() {
    const ctx = useContext(TutorialContext);
    if (!ctx) {
        throw new Error("useTutorial must be used within TutorialProvider");
    }
    return ctx;
}

// ─────────────────────────────────────────────────────────────────────────────
// Provider
// ─────────────────────────────────────────────────────────────────────────────

interface TutorialProviderProps {
    children: React.ReactNode;
}

export function TutorialProvider({ children }: TutorialProviderProps) {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();

    // Active flow state
    const [activeFlowId, setActiveFlowId] = useState<string | null>(null);
    const [localStepIndex, setLocalStepIndex] = useState(0);

    // Fetch flow data when active
    const { data: flowData, refetch } = useOnboardingStatus(activeFlowId || "");
    const actions = useOnboardingActions();

    // Check URL for tutorial param on mount
    useEffect(() => {
        const tutorialParam = searchParams.get("tutorial");
        if (tutorialParam && !activeFlowId) {
            setActiveFlowId(tutorialParam);
            // Remove param from URL without navigation
            const url = new URL(window.location.href);
            url.searchParams.delete("tutorial");
            window.history.replaceState({}, "", url.toString());
        }
    }, [searchParams, activeFlowId]);

    // Sync local step with server state
    useEffect(() => {
        if (flowData?.progress) {
            const serverStep = flowData.progress.current_step;
            // If server is ahead (e.g., resuming), use server step
            if (serverStep > 0 && serverStep !== localStepIndex) {
                setLocalStepIndex(serverStep);
            }
        }
    }, [flowData?.progress?.current_step]);

    // Current step derived from flow data
    const currentStep = useMemo(() => {
        if (!flowData?.flow?.steps || localStepIndex <= 0) return null;
        const idx = localStepIndex - 1; // steps are 1-indexed in backend
        return flowData.flow.steps[idx] || null;
    }, [flowData, localStepIndex]);

    const isActive = !!activeFlowId && !!currentStep;
    const totalSteps = flowData?.flow?.total_steps || 0;

    // ─────────────────────────────────────────────────────────────────────────
    // Actions
    // ─────────────────────────────────────────────────────────────────────────

    const startFlow = useCallback(
        async (flowId: string, replay: boolean = false) => {
            try {
                const result = await actions.startFlow({ flowId, replay });
                setActiveFlowId(flowId);
                setLocalStepIndex(result.current_step);
                await refetch();
            } catch (error) {
                console.error("[Tutorial] Failed to start flow:", error);
            }
        },
        [actions, refetch]
    );

    const nextStep = useCallback(async () => {
        if (!activeFlowId || !flowData?.flow) return;

        const nextStepIndex = localStepIndex + 1;
        const isLastStep = nextStepIndex > flowData.flow.total_steps;

        // ✨ Optimistic: Update UI immediately
        if (isLastStep) {
            // Flow complete - close immediately
            const ctaHref = currentStep?.cta?.href;
            setActiveFlowId(null);
            setLocalStepIndex(0);

            // Navigate if CTA
            if (ctaHref) {
                router.push(ctaHref);
            }
        } else {
            // Advance to next step immediately
            setLocalStepIndex(nextStepIndex);
        }

        // 🔄 Fire API in background (non-blocking)
        actions.completeStep(activeFlowId).catch((error) => {
            console.error("[Tutorial] Failed to complete step:", error);
            // Note: We don't rollback UI - persist best-effort
        });
    }, [activeFlowId, flowData, localStepIndex, currentStep, router, actions]);

    const skipFlow = useCallback(async () => {
        if (!activeFlowId) return;

        // ✨ Optimistic: Close immediately
        setActiveFlowId(null);
        setLocalStepIndex(0);

        // 🔄 Fire API in background (non-blocking)
        actions.skipFlow(activeFlowId).catch((error) => {
            console.error("[Tutorial] Failed to skip flow:", error);
        });
    }, [activeFlowId, actions]);

    const closeTutorial = useCallback(() => {
        setActiveFlowId(null);
        setLocalStepIndex(0);
    }, []);

    // ─────────────────────────────────────────────────────────────────────────
    // Context Value
    // ─────────────────────────────────────────────────────────────────────────

    const value = useMemo<TutorialContextValue>(
        () => ({
            isActive,
            flowId: activeFlowId,
            currentStep,
            stepIndex: localStepIndex,
            totalSteps,
            progress: flowData || null,
            startFlow,
            nextStep,
            skipFlow,
            closeTutorial,
        }),
        [
            isActive,
            activeFlowId,
            currentStep,
            localStepIndex,
            totalSteps,
            flowData,
            startFlow,
            nextStep,
            skipFlow,
            closeTutorial,
        ]
    );

    return (
        <TutorialContext.Provider value={value}>
            {children}
        </TutorialContext.Provider>
    );
}
