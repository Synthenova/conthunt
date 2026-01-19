"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { Flame, Gift, Shirt, Package, Plane, Check } from 'lucide-react';
import type { StreakMilestone as MilestoneType } from '@/hooks/useStreak';

interface StreakMilestoneProps {
    currentStreak: number;
    nextMilestone: MilestoneType | null;
    milestones: MilestoneType[];
    className?: string;
}

// Map icon names to Lucide icons
const iconMap: Record<string, React.ElementType> = {
    gift: Gift,
    shirt: Shirt,
    package: Package,
    plane: Plane,
};

export function StreakMilestone({
    currentStreak,
    nextMilestone,
    milestones = [],
    className
}: StreakMilestoneProps) {
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
                <div className="relative">
                    {/* Connection Line */}
                    <div className="absolute top-6 left-0 right-0 h-0.5 bg-gray-700 z-0" />

                    {/* Progress Line - fills based on progress */}
                    <div
                        className="absolute top-6 left-0 h-0.5 bg-orange-400 z-0 transition-all duration-500"
                        style={{
                            width: milestones.length > 0
                                ? `${Math.min(
                                    ((milestones.filter(m => m.completed).length) / milestones.length) * 100,
                                    100
                                )}%`
                                : '0%'
                        }}
                    />

                    {/* Milestone Items */}
                    <div className="relative z-10 flex justify-between">
                        {/* Start Point */}
                        <div className="flex flex-col items-center">
                            <div className={cn(
                                "w-12 h-12 rounded-full border-2 flex items-center justify-center",
                                currentStreak > 0
                                    ? "border-orange-400 bg-orange-400/10 text-orange-400"
                                    : "border-gray-600 bg-gray-800 text-gray-500"
                            )}>
                                <Check className="h-5 w-5" />
                            </div>
                            <span className="text-xs text-gray-400 mt-2">Start</span>
                        </div>

                        {/* Milestone Points */}
                        {milestones.map((milestone) => {
                            const Icon = iconMap[milestone.icon_name] || Gift;
                            const isCompleted = milestone.completed;
                            const isNext = nextMilestone?.days_required === milestone.days_required;

                            return (
                                <div key={milestone.days_required} className="flex flex-col items-center">
                                    <div className={cn(
                                        "w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all",
                                        isCompleted
                                            ? "border-orange-400 bg-orange-400/10 text-orange-400"
                                            : isNext
                                                ? "border-gray-500 bg-gray-800 text-gray-400 ring-2 ring-orange-400/30"
                                                : "border-gray-600 bg-gray-800 text-gray-500"
                                    )}>
                                        <Icon className="h-5 w-5" />
                                    </div>
                                    <div className="text-center mt-2">
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
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}
