import { useState, useEffect, useCallback } from "react";

/**
 * Hook to find a target element and return its bounding client rect.
 * Uses MutationObserver to detect when the element appears in the DOM.
 */
export function useTutorialTarget(selector: string | null) {
    const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
    const [targetElement, setTargetElement] = useState<Element | null>(null);

    const updateRect = useCallback(() => {
        if (!selector) {
            setTargetRect(null);
            setTargetElement(null);
            return;
        }

        const element = document.querySelector(selector);
        if (element) {
            setTargetRect(element.getBoundingClientRect());
            setTargetElement(element);
        } else {
            setTargetRect(null);
            setTargetElement(null);
        }
    }, [selector]);

    // Initial check and periodic polling + MutationObserver
    useEffect(() => {
        if (!selector) return;

        // 1. Initial check
        updateRect();

        // 2. Observer for DOM changes (robust detection)
        const observer = new MutationObserver(() => {
            updateRect();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true, // In case attributes change to match selector
        });

        // 3. Resize listener to update rect position
        window.addEventListener("resize", updateRect);
        window.addEventListener("scroll", updateRect, { capture: true, passive: true });

        return () => {
            observer.disconnect();
            window.removeEventListener("resize", updateRect);
            window.removeEventListener("scroll", updateRect);
        };
    }, [selector, updateRect]);

    // Scroll into view when element is first found
    useEffect(() => {
        if (targetElement) {
            const rect = targetElement.getBoundingClientRect();
            // Only scroll if out of viewport
            if (rect.top < 0 || rect.bottom > window.innerHeight) {
                targetElement.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        }
    }, [targetElement]);

    return { targetRect, targetElement };
}
