"use client";

import React, { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Flame, Gift, Check, Loader2 } from 'lucide-react';
import type { StreakMilestone as MilestoneType } from '@/hooks/useStreak';

interface StreakMilestoneProps {
    currentStreak: number;
    nextMilestone: MilestoneType | null;
    milestones: MilestoneType[];
    className?: string;
    onClaim?: (daysRequired: number) => void;
    isClaiming?: boolean;
}

export function StreakMilestone({
    currentStreak,
    nextMilestone,
    milestones = [],
    className,
    onClaim,
    isClaiming,
}: StreakMilestoneProps) {
    const [claimingDays, setClaimingDays] = useState<number | null>(null);

    useEffect(() => {
        if (!isClaiming) {
            setClaimingDays(null);
        }
    }, [isClaiming]);

    const lastCompleted = [...milestones].reverse().find((m) => m.completed);
    const maxDays = milestones[milestones.length - 1]?.days_required ?? 0;
    const completedMilestoneIndex = milestones.reduce(
        (acc, milestone, index) => (milestone.completed ? index : acc),
        -1
    );
    const completedIndex = completedMilestoneIndex >= 0 ? completedMilestoneIndex + 1 : 0;
    const nodes = [
        { key: 'start', type: 'start' as const },
        ...milestones.map((milestone) => ({
            key: milestone.days_required,
            type: 'milestone' as const,
            milestone,
        })),
    ];
    const gridTemplateColumns = Array.from(
        { length: nodes.length * 2 - 1 },
        (_, index) => (index % 2 === 0 ? 'auto' : '1fr')
    ).join(' ');

    return (
        <div className={cn("w-full", className)}>
            {/* Top Section - Current Streak & Next Milestone */}
            <div className="bg-[#0d1117] border border-white/10 rounded-xl p-6 mb-6">
                <div className="flex items-center justify-between">
                    {/* Current Streak */}
                    <div>
                        <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Your Current Streak</p>
                        <div className="flex items-center gap-2">
                            <Flame className="h-6 w-6 text-orange-400" />
                            <span className="text-3xl font-bold text-white">
                                {currentStreak} {currentStreak === 1 ? 'day' : 'days'}
                            </span>
                        </div>
                    </div>

                    {/* Next Milestone */}
                    {nextMilestone && (
                        <div className="text-right">
                            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Next Milestone</p>
                            <span className="text-2xl font-bold text-white">
                                {nextMilestone.days_required} days
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Rewards Section */}
            <div className="bg-[#0d1117] border border-white/10 rounded-xl p-6">
                <h3 className="text-center text-sm font-semibold text-white mb-8">Rewards</h3>

                {/* Milestone Timeline */}
                <div
                    className="grid gap-x-3 gap-y-2"
                    style={{ gridTemplateColumns: gridTemplateColumns }}
                >
                    {nodes.map((node, index) => {
                        const gridColumn = index * 2 + 1;
                        if (node.type === 'start') {
                            return (
                                <React.Fragment key={node.key}>
                                    <div
                                        className={cn(
                                            "w-12 h-12 rounded-full border-2 flex items-center justify-center justify-self-center",
                                            currentStreak > 0
                                                ? "border-orange-400 bg-orange-400/10 text-orange-400"
                                                : "border-gray-600 bg-gray-800 text-gray-500"
                                        )}
                                        style={{ gridColumn, gridRow: 1 }}
                                    >
                                        <Check className="h-5 w-5" />
                                    </div>
                                    <span
                                        className="text-xs text-gray-400 text-center"
                                        style={{ gridColumn, gridRow: 2 }}
                                    >
                                        Start
                                    </span>
                                </React.Fragment>
                            );
                        }

                        const milestone = node.milestone;
                        const isCompleted = milestone.completed;
                        const isNext = nextMilestone?.days_required === milestone.days_required;
                        const isClaimable = milestone.claimable;
                        const isClaimed = milestone.claimed;
                        const isLoading = isClaiming && claimingDays === milestone.days_required;

                        return (
                            <React.Fragment key={node.key}>
                                <button
                                    type="button"
                                    disabled={!isClaimable || isClaiming}
                                    onClick={() => {
                                        if (!isClaimable || isClaiming) return;
                                        setClaimingDays(milestone.days_required);
                                        onClaim?.(milestone.days_required);
                                    }}
                                    className={cn(
                                        "w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all justify-self-center",
                                        isCompleted
                                            ? "border-orange-400 bg-orange-400/10 text-orange-400"
                                            : isNext
                                                ? "border-gray-500 bg-gray-800 text-gray-400 ring-2 ring-orange-400/30"
                                                : "border-gray-600 bg-gray-800 text-gray-500",
                                        isClaimable && "cursor-pointer hover:border-orange-300 hover:text-orange-300",
                                        isClaimed && "opacity-60",
                                        isClaimable && "ring-2 ring-orange-400/40 shadow-[0_0_16px_rgba(251,146,60,0.45)]",
                                        (!isClaimable || isClaiming) && "cursor-default"
                                    )}
                                    style={{ gridColumn, gridRow: 1 }}
                                >
                                    {isLoading ? (
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                    ) : (
                                        <Gift className="h-5 w-5" />
                                    )}
                                </button>
                                <div
                                    className="text-center"
                                    style={{ gridColumn, gridRow: 2 }}
                                >
                                    <p className={cn(
                                        "text-sm font-semibold",
                                        isCompleted ? "text-orange-400" : "text-white"
                                    )}>
                                        {milestone.days_required} Days
                                    </p>
                                    <p className="text-xs text-gray-500 max-w-[80px] leading-tight">
                                        {milestone.reward_description}
                                    </p>
                                </div>
                            </React.Fragment>
                        );
                    })}

                    {nodes.slice(0, -1).map((node, index) => {
                        const gridColumn = index * 2 + 2;
                        const isFilled = index < completedIndex;
                        return (
                            <div
                                key={`${node.key}-line`}
                                className={cn(
                                    "h-0.5 self-center",
                                    isFilled ? "bg-orange-400" : "bg-gray-700"
                                )}
                                style={{ gridColumn, gridRow: 1 }}
                            />
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
