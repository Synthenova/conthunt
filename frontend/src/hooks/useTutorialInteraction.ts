import { useEffect, useRef } from "react";
import { InteractionType } from "@/config/tutorialTargets";

interface UseTutorialInteractionOptions {
    targetElement: Element | null;
    interactionType: InteractionType;
    onInteraction: () => void;
    enabled: boolean;
}

/**
 * Hook to listen for user interactions on the target element.
 * Auto-advances the tutorial when the interaction occurs.
 */
export function useTutorialInteraction({
    targetElement,
    interactionType,
    onInteraction,
    enabled
}: UseTutorialInteractionOptions) {
    // Prevent double firing
    const hasFiredRef = useRef(false);

    // Reset fired state when target or step changes
    useEffect(() => {
        hasFiredRef.current = false;
    }, [targetElement, interactionType]);

    useEffect(() => {
        if (!enabled || !targetElement || interactionType === "next_button") return;
        if (hasFiredRef.current) return;

        const handleInteraction = (e: Event) => {
            // For submit events, we might want to let them bubble first?
            // But usually we want to catch it immediately.

            console.log("[Tutorial] Interaction detected:", interactionType);
            hasFiredRef.current = true;
            onInteraction();
        };

        const eventsMap: Record<InteractionType, string> = {
            click: 'click',
            focus: 'focus',
            input: 'input', // or change?
            submit: 'submit',
            next_button: '', // Handled manually
        };

        const eventName = eventsMap[interactionType];
        if (!eventName) return;

        // Use capture phase to ensure we catch it before app logic might stop propagation?
        // Or bubble phase? Capture is safer for tracking.
        targetElement.addEventListener(eventName, handleInteraction, { capture: true });

        // For 'input', maybe we wait for a debounce or 'blur'?
        // User asked for "focus / type". Focus is easiest.

        return () => {
            targetElement.removeEventListener(eventName, handleInteraction, { capture: true });
        };
    }, [targetElement, interactionType, onInteraction, enabled]);
}
