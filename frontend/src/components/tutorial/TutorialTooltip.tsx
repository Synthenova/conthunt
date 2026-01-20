/**
 * Tutorial Tooltip Component
 * Glass-style tooltip with smart positioning and animations.
 */
"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronRight, SkipForward } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTutorial } from "./TutorialProvider";
import { cn } from "@/lib/utils";
import { getTutorialTarget, getTutorialInteraction } from "@/config/tutorialTargets";
import { useTutorialTarget } from "@/hooks/useTutorialTarget";
import { useTutorialInteraction } from "@/hooks/useTutorialInteraction";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

type Position = "top" | "bottom" | "left" | "right" | "center";

interface TooltipPosition {
    x: number;
    y: number;
    position: Position;
}

// ─────────────────────────────────────────────────────────────────────────────
// Position Calculation
// ─────────────────────────────────────────────────────────────────────────────

const TOOLTIP_WIDTH = 320;
const TOOLTIP_HEIGHT = 180;
const OFFSET = 16;
const EDGE_PADDING = 16;

function calculatePosition(targetRect: DOMRect | null): TooltipPosition {
    // No target = center modal
    if (!targetRect) {
        return {
            x: window.innerWidth / 2 - TOOLTIP_WIDTH / 2,
            y: window.innerHeight / 2 - TOOLTIP_HEIGHT / 2,
            position: "center",
        };
    }

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Calculate available space in each direction
    const spaceTop = targetRect.top;
    const spaceBottom = viewportHeight - targetRect.bottom;
    const spaceLeft = targetRect.left;
    const spaceRight = viewportWidth - targetRect.right;

    // Determine best position (prefer bottom, then top, then right, then left)
    let position: Position = "bottom";
    let x = 0;
    let y = 0;

    if (spaceBottom >= TOOLTIP_HEIGHT + OFFSET) {
        position = "bottom";
        x = targetRect.left + targetRect.width / 2 - TOOLTIP_WIDTH / 2;
        y = targetRect.bottom + OFFSET;
    } else if (spaceTop >= TOOLTIP_HEIGHT + OFFSET) {
        position = "top";
        x = targetRect.left + targetRect.width / 2 - TOOLTIP_WIDTH / 2;
        y = targetRect.top - TOOLTIP_HEIGHT - OFFSET;
    } else if (spaceRight >= TOOLTIP_WIDTH + OFFSET) {
        position = "right";
        x = targetRect.right + OFFSET;
        y = targetRect.top + targetRect.height / 2 - TOOLTIP_HEIGHT / 2;
    } else if (spaceLeft >= TOOLTIP_WIDTH + OFFSET) {
        position = "left";
        x = targetRect.left - TOOLTIP_WIDTH - OFFSET;
        y = targetRect.top + targetRect.height / 2 - TOOLTIP_HEIGHT / 2;
    } else {
        // Fallback: position below with clamping
        position = "bottom";
        x = targetRect.left + targetRect.width / 2 - TOOLTIP_WIDTH / 2;
        y = targetRect.bottom + OFFSET;
    }

    // Clamp to viewport bounds
    x = Math.max(EDGE_PADDING, Math.min(x, viewportWidth - TOOLTIP_WIDTH - EDGE_PADDING));
    y = Math.max(EDGE_PADDING, Math.min(y, viewportHeight - TOOLTIP_HEIGHT - EDGE_PADDING));

    return { x, y, position };
}

// ─────────────────────────────────────────────────────────────────────────────
// Spotlight Overlay
// ─────────────────────────────────────────────────────────────────────────────

function SpotlightOverlay({ targetRect }: { targetRect: DOMRect | null }) {
    if (!targetRect) {
        return (
            <div className="fixed inset-0 bg-black/60 z-[9998]" />
        );
    }

    const padding = 8;

    return (
        <div className="fixed inset-0 z-[9998] pointer-events-none">
            {/* Dark overlay with cutout */}
            <svg className="w-full h-full">
                <defs>
                    <mask id="spotlight-mask">
                        <rect x="0" y="0" width="100%" height="100%" fill="white" />
                        <rect
                            x={targetRect.left - padding}
                            y={targetRect.top - padding}
                            width={targetRect.width + padding * 2}
                            height={targetRect.height + padding * 2}
                            rx="12"
                            fill="black"
                        />
                    </mask>
                </defs>
                <rect
                    x="0"
                    y="0"
                    width="100%"
                    height="100%"
                    fill="rgba(0, 0, 0, 0.6)"
                    mask="url(#spotlight-mask)"
                />
            </svg>
            {/* Highlight ring around target */}
            <div
                className="absolute rounded-xl border-2 border-primary shadow-[0_0_20px_rgba(255,255,255,0.3)] transition-all duration-300"
                style={{
                    left: targetRect.left - padding,
                    top: targetRect.top - padding,
                    width: targetRect.width + padding * 2,
                    height: targetRect.height + padding * 2,
                }}
            />
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export function TutorialTooltip() {
    const {
        isActive,
        flowId,
        currentStep,
        stepIndex,
        totalSteps,
        nextStep,
        skipFlow,
        closeTutorial,
    } = useTutorial();

    const [position, setPosition] = useState<TooltipPosition>({ x: 0, y: 0, position: "center" });
    const tooltipRef = useRef<HTMLDivElement>(null);

    // 1. Get configuration
    const targetSelector = flowId && currentStep?.id
        ? getTutorialTarget(flowId, currentStep.id)
        : null;

    const interactionType = flowId && currentStep?.id
        ? getTutorialInteraction(flowId, currentStep.id)
        : "next_button";

    // 2. Find target with robust retry logic
    const { targetRect, targetElement } = useTutorialTarget(targetSelector);

    // 3. Handle user interactions (click, focus, etc)
    useTutorialInteraction({
        targetElement,
        interactionType,
        onInteraction: nextStep,
        enabled: isActive
    });

    // 4. Calculate position when target changes
    useEffect(() => {
        if (!isActive) return;
        setPosition(calculatePosition(targetRect));
    }, [isActive, targetRect]);

    // 5. Strict Waiting: If target is missing but expected, don't show anything
    // We removed the fallback logic as requested.

    // Check if we are waiting for a target
    const isWaitingForTarget = !!targetSelector && !targetRect;
    const isLastStep = stepIndex >= totalSteps;

    // Determine if we should show the next button
    const shouldShowNext =
        interactionType === "next_button" ||
        isLastStep;

    if (!isActive || !currentStep) return null;

    // If we have a selector but no rect, we are strictly waiting. Hide.
    if (isWaitingForTarget) return null;

    // Portal to body to ensure it's on top of everything (including Drawers/Modals)
    if (typeof document === 'undefined') return null;

    return createPortal(
        <>
            {/* Spotlight overlay */}
            <SpotlightOverlay targetRect={targetRect} />

            {/* Tooltip */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={`step-${stepIndex}`}
                    ref={tooltipRef}
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -10 }}
                    transition={{ duration: 0.25, ease: "easeOut" }}
                    className={cn(
                        "fixed z-[9999] w-[320px] pointer-events-auto",
                        "tutorial-tooltip",
                        "rounded-2xl p-5",
                        "shadow-2xl shadow-black/50"
                    )}
                    style={{
                        left: position.x,
                        top: position.y,
                    }}
                >
                    {/* Close button */}
                    <button
                        onClick={closeTutorial}
                        className="absolute top-3 right-3 p-1 rounded-full hover:bg-white/10 transition-colors"
                    >
                        <X className="h-4 w-4 text-gray-400" />
                    </button>

                    {/* Content */}
                    <div className="space-y-3">
                        {/* Step counter */}
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] uppercase tracking-widest text-gray-500 font-bold">
                                Step {stepIndex} of {totalSteps}
                            </span>
                        </div>

                        {/* Title */}
                        <h3 className="text-lg font-semibold text-white pr-6">
                            {currentStep.title}
                        </h3>

                        {/* Description */}
                        <p className="text-sm text-gray-400 leading-relaxed">
                            {currentStep.content}
                        </p>

                        {/* Actions */}
                        <div className="flex items-center justify-between pt-2">
                            <button
                                onClick={skipFlow}
                                className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
                            >
                                <SkipForward className="h-3 w-3" />
                                Skip tutorial
                            </button>

                            {shouldShowNext && (
                                <Button
                                    onClick={nextStep}
                                    size="sm"
                                    className="glass-button-white px-4 h-8 text-xs font-medium"
                                >
                                    {isLastStep ? (
                                        currentStep.cta?.label || "Finish"
                                    ) : (
                                        <>
                                            Next
                                            <ChevronRight className="h-3 w-3 ml-1" />
                                        </>
                                    )}
                                </Button>
                            )}
                        </div>
                    </div>

                    {/* Progress dots */}
                    <div className="flex items-center justify-center gap-1.5 mt-4">
                        {Array.from({ length: totalSteps }).map((_, i) => (
                            <div
                                key={i}
                                className={cn(
                                    "w-1.5 h-1.5 rounded-full transition-colors",
                                    i + 1 === stepIndex
                                        ? "bg-white"
                                        : i + 1 < stepIndex
                                            ? "bg-white/50"
                                            : "bg-white/20"
                                )}
                            />
                        ))}
                    </div>
                </motion.div>
            </AnimatePresence>
        </>,
        document.body
    );
}
