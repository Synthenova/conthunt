"use client";

import React, { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Flame, Gift, Check, Loader2 } from 'lucide-react';
import type { StreakMilestone as MilestoneType } from '@/hooks/useStreak';

import { Skeleton } from "@/components/ui/skeleton";

interface StreakMilestoneProps {
    currentStreak: number;
    nextMilestone: MilestoneType | null;
    milestones: MilestoneType[];
    className?: string;
    onClaim?: (daysRequired: number) => void;
    isClaiming?: boolean;
    todayProgress?: React.ReactNode;
    isLoading?: boolean;
}

export function StreakMilestone({
    currentStreak,
    nextMilestone,
    milestones = [],
    className,
    onClaim,
    isClaiming,
    todayProgress,
    isLoading = false,
}: StreakMilestoneProps) {
    const [claimingDays, setClaimingDays] = useState<number | null>(null);

    useEffect(() => {
        if (!isClaiming) {
            setClaimingDays(null);
        }
    }, [isClaiming]);

    // Construct the timeline nodes: Start (0) + Milestones
    const allNodes = [
        { days_required: 0, reward_description: "Start", completed: true, claimable: false, claimed: false },
        ...milestones
    ];

    return (
        <div className={cn("w-full space-y-6", className)}>
            {/* Header Section: Current Streak & Next Goal */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 px-2">
                <div>
                    <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground mb-2">Current Streak</p>
                    <div className="flex items-center gap-3">
                        {isLoading ? (
                            <Skeleton className="h-12 w-16 bg-white/10 rounded-md" />
                        ) : (
                            <span className="text-5xl font-bold text-foreground tracking-tight">
                                {currentStreak}
                            </span>
                        )}

                        <div className="p-2 bg-orange-500/10 rounded-full animate-pulse">
                            <Flame className="h-6 w-6 text-orange-500 fill-orange-500 animate-bounce" />
                        </div>
                    </div>
                </div>

                <div className="md:text-right pb-2">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground mb-1">Next Goal</p>
                    {isLoading ? (
                        <div className="flex flex-col items-end gap-1">
                            <Skeleton className="h-7 w-24 bg-white/10 rounded-md" />
                        </div>
                    ) : nextMilestone ? (
                        <span className="text-xl font-bold text-foreground">
                            {nextMilestone.days_required} <span className="text-sm text-muted-foreground font-normal ml-1">days</span>
                        </span>
                    ) : (
                        <span className="text-sm text-muted-foreground">Max streak reached!</span>
                    )}
                </div>
            </div>

            {/* Card Content: Timeline + Daily Progress */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 md:p-8 backdrop-blur-sm">
                {/* Timeline */}
                <div className="relative pt-4 pb-8">
                    {isLoading ? (
                        <div className="flex items-center justify-between w-full relative z-10">
                            {/* Start Node Skeleton */}
                            <div className="flex flex-col items-center gap-2">
                                <Skeleton className="w-10 h-10 rounded-full bg-white/10" />
                                <Skeleton className="h-3 w-8 bg-white/10" />
                            </div>

                            {/* Line */}
                            <Skeleton className="h-1 flex-grow mx-2 bg-white/10 rounded-full" />

                            {/* Milestone 1 */}
                            <div className="flex flex-col items-center gap-2">
                                <Skeleton className="w-10 h-10 rounded-full bg-white/10" />
                                <Skeleton className="h-3 w-12 bg-white/10" />
                            </div>

                            {/* Line */}
                            <Skeleton className="h-1 flex-grow mx-2 bg-white/10 rounded-full" />

                            {/* Milestone 2 */}
                            <div className="flex flex-col items-center gap-2">
                                <Skeleton className="w-10 h-10 rounded-full bg-white/10" />
                                <Skeleton className="h-3 w-12 bg-white/10" />
                            </div>
                            {/* Line */}
                            <Skeleton className="h-1 flex-grow mx-2 bg-white/10 rounded-full" />

                            {/* Milestone 3 */}
                            <div className="flex flex-col items-center gap-2">
                                <Skeleton className="w-10 h-10 rounded-full bg-white/10" />
                                <Skeleton className="h-3 w-12 bg-white/10" />
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center justify-between w-full relative z-10">
                            {allNodes.map((node, index) => {
                                // Check if this is the last node
                                const isLast = index === allNodes.length - 1;
                                const nextNode = !isLast ? allNodes[index + 1] : null;

                                // Calculate progress for the line following this node
                                let lineProgress = 0;
                                let flexGrow = 0;

                                if (nextNode) {
                                    const range = nextNode.days_required - node.days_required;
                                    flexGrow = Math.max(range, 2);
                                    const progressInSegment = Math.max(0, currentStreak - node.days_required);
                                    lineProgress = Math.min(100, (progressInSegment / range) * 100);
                                }

                                const isCompleted = node.days_required <= currentStreak;
                                const isClaimabl = 'claimable' in node ? node.claimable : false;
                                const isClaimed = 'claimed' in node ? node.claimed : false;
                                const isLoading = isClaiming && claimingDays === node.days_required;

                                // For the start node (0 days)
                                if (node.days_required === 0) {
                                    return (
                                        <React.Fragment key={node.days_required}>
                                            <div className="relative flex flex-col items-center group">
                                                <div className="w-10 h-10 rounded-full bg-white/10 border-2 border-white/20 flex items-center justify-center z-20 shadow-[0_0_20px_rgba(255,255,255,0.05)]">
                                                    <Check className="w-5 h-5 text-white" strokeWidth={3} />
                                                </div>
                                                <div className="absolute top-14 left-1/2 -translate-x-1/2 whitespace-nowrap">
                                                    <span className="text-xs font-semibold text-muted-foreground">Start</span>
                                                </div>
                                            </div>

                                            {!isLast && (
                                                <div
                                                    className="h-1 bg-white/10 relative mx-2 rounded-full overflow-hidden"
                                                    style={{ flexGrow: flexGrow, flexBasis: '2rem' }}
                                                >
                                                    <div
                                                        className="absolute inset-y-0 left-0 bg-white/80 shadow-[0_0_15px_rgba(255,255,255,0.5)] transition-all duration-1000 ease-out"
                                                        style={{ width: `${lineProgress}%` }}
                                                    />
                                                </div>
                                            )}
                                        </React.Fragment>
                                    );
                                }

                                // Milestone Nodes
                                return (
                                    <React.Fragment key={node.days_required}>
                                        <div className="relative flex flex-col items-center">
                                            <button
                                                type="button"
                                                disabled={!isClaimabl || isClaiming || isClaimed}
                                                onClick={() => {
                                                    if (!isClaimabl || isClaiming || isClaimed) return;
                                                    setClaimingDays(node.days_required);
                                                    onClaim?.(node.days_required);
                                                }}
                                                className={cn(
                                                    "w-10 h-10 rounded-full flex items-center justify-center transition-all z-20 border-2",
                                                    // Claimed: Simple White tick
                                                    isClaimed && "bg-white/20 border-white/40 text-white shadow-[0_0_20px_rgba(255,255,255,0.1)]",
                                                    // Claimable: Bright Glass + Pulse
                                                    isClaimabl && !isClaimed && !isLoading && "bg-white/10 border-white/60 text-white hover:bg-white/20 hover:scale-110 shadow-[0_0_25px_rgba(255,255,255,0.4)] cursor-pointer animate-pulse",
                                                    // Future/Locked: Dim Glass
                                                    !isClaimabl && !isClaimed && "bg-white/5 border-white/10 text-muted-foreground",
                                                    // Loading
                                                    isLoading && "bg-white/10 border-white/50 text-white",
                                                    "backdrop-blur-md"
                                                )}
                                            >
                                                {isLoading ? (
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                ) : isClaimed ? (
                                                    <Check className="h-5 w-5" strokeWidth={3} />
                                                ) : (
                                                    <Gift className={cn("h-4 w-4", isClaimabl && "fill-current")} />
                                                )}
                                            </button>

                                            <div className="absolute top-14 left-1/2 -translate-x-1/2 flex flex-col items-center w-[120px]">
                                                <span className={cn(
                                                    "text-xs font-bold whitespace-nowrap mb-0.5",
                                                    isCompleted ? "text-foreground" : "text-muted-foreground"
                                                )}>
                                                    {node.days_required} Days
                                                </span>
                                                <span className="text-[10px] text-muted-foreground text-center leading-tight">
                                                    {node.reward_description}
                                                </span>
                                            </div>
                                        </div>

                                        {!isLast && (
                                            <div
                                                className="h-1 bg-white/10 relative mx-2 rounded-full overflow-hidden"
                                                style={{ flexGrow: flexGrow, flexBasis: '2rem' }}
                                            >
                                                <div
                                                    className="absolute inset-y-0 left-0 bg-white/80 shadow-[0_0_15px_rgba(255,255,255,0.5)] transition-all duration-1000 ease-out"
                                                    style={{ width: `${lineProgress}%` }}
                                                />
                                            </div>
                                        )}
                                    </React.Fragment>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Daily Progress Slot */}
                {isLoading ? (
                    <div className="mt-8 pt-6 border-t border-white/10 grid grid-cols-2 gap-4">
                        <Skeleton className="h-16 w-full rounded-xl bg-white/5" />
                        <Skeleton className="h-16 w-full rounded-xl bg-white/5" />
                    </div>
                ) : todayProgress && (
                    <div className="mt-8 pt-6 border-t border-white/10">
                        {todayProgress}
                    </div>
                )}
            </div>
        </div>
    );
}
