/**
 * Tutorial Auto-Start Hook
 * Automatically starts or resumes a tutorial flow when a page loads.
 */
"use client";

import { useEffect, useRef } from "react";
import { useOnboardingStatus } from "@/hooks/useOnboarding";
import { useTutorial } from "@/components/tutorial/TutorialProvider";
import { auth } from "@/lib/firebaseClient";

interface UseTutorialAutoStartOptions {
    /** Flow ID to auto-start */
    flowId: string;
    /** Delay in ms before starting (allows page to render) */
    delay?: number;
    /** Only auto-start if this condition is true */
    enabled?: boolean;
}

/**
 * Hook to automatically start or resume a tutorial flow when visiting a page.
 * Starts if not_started, resumes if in_progress.
 */
export function useTutorialAutoStart({
    flowId,
    delay = 500,
    enabled = true,
}: UseTutorialAutoStartOptions) {
    const { data: flowData, isLoading } = useOnboardingStatus(flowId);
    const { startFlow, isActive, flowId: activeFlowId } = useTutorial();
    const hasTriggeredRef = useRef(false);

    useEffect(() => {
        // Guard conditions
        if (!enabled) return;
        if (!auth?.currentUser) return;
        if (isLoading) return;
        if (hasTriggeredRef.current) return;
        if (isActive && activeFlowId === flowId) return; // Already active for this flow

        const status = flowData?.progress?.status;

        // Start if not_started, OR resume if in_progress
        if (status === "not_started" || status === "in_progress") {
            hasTriggeredRef.current = true;

            const timeoutId = setTimeout(() => {
                startFlow(flowId, false).catch((error) => {
                    console.error("[Tutorial] Failed to auto-start:", error);
                    hasTriggeredRef.current = false;
                });
            }, delay);

            return () => clearTimeout(timeoutId);
        }
    }, [enabled, flowId, flowData, isLoading, delay, startFlow, isActive, activeFlowId]);

    return {
        status: flowData?.progress?.status,
        isLoading,
    };
}
