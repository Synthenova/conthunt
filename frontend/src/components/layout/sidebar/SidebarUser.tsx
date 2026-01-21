"use client";

import React, { useState } from 'react';
import { LogoutIcon, type LogoutIconHandle } from '@/components/ui/logout';
import { cn } from '@/lib/utils';
import { LogoutButton } from "@/components/logout-button";
import { useRouter } from 'next/navigation';
import { useProducts } from '@/contexts/ProductsContext';
import { FeedbackModal } from '@/components/modals/FeedbackModal';
import { GiftShareModal } from '@/components/modals/GiftShareModal';
import { Flame } from 'lucide-react';
import { motion } from "framer-motion";
import { useStreak } from "@/hooks/useStreak";

interface SidebarUserProps {
    user: any;
    profile: any;
    isCollapsed: boolean;
}

export const SidebarUser = ({ user, profile, isCollapsed }: SidebarUserProps) => {
    const router = useRouter();
    const { getPlanName, loading: productsLoading } = useProducts();
    const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
    const [isGiftOpen, setIsGiftOpen] = useState(false);
    const { streak: streakData } = useStreak();

    const planDisplayName = profile?.role
        ? getPlanName(profile.role)
        : (productsLoading ? "Loading..." : "Free");

    return (
        <div className="p-4 border-t border-white/5 mt-auto space-y-2">
            {/* Streak Item - Moved from Sidebar */}
            {streakData && streakData.current_streak > 0 && (
                <button
                    onClick={() => router.push('/app/profile')}
                    className={cn(
                        "flex items-center rounded-xl hover:bg-white/5 cursor-pointer group transition-all text-white p-2 border border-transparent hover:border-white/5",
                        isCollapsed ? "justify-center aspect-square w-full" : "space-x-3 w-full"
                    )}
                    title="View Streak"
                >
                    <div className={cn("flex items-center justify-center shrink-0 w-8 h-8", isCollapsed ? "" : "w-8")}>
                        <div className="relative">
                            <motion.div
                                animate={{
                                    scale: [1, 1.1, 1],
                                    rotate: [0, -5, 5, -5, 0],
                                }}
                                transition={{
                                    duration: 0.6,
                                    repeat: Infinity,
                                    repeatDelay: 3,
                                }}
                            >
                                <Flame className="h-5 w-5 text-white" />
                            </motion.div>
                            <span className="absolute -top-1 -right-1 text-[8px] font-bold text-white">
                                {streakData.current_streak}
                            </span>
                        </div>
                    </div>
                    {!isCollapsed && (
                        <span className="text-xs font-semibold text-white">
                            {streakData.current_streak} day{streakData.current_streak !== 1 ? 's' : ''} streak
                        </span>
                    )}
                </button>
            )}

            <button
                onClick={() => setIsGiftOpen(true)}
                className={cn(
                    "flex items-center rounded-xl hover:bg-white/5 cursor-pointer group transition-all text-gray-300 hover:text-emerald-400 p-2 border border-transparent hover:border-white/5",
                    isCollapsed ? "justify-center aspect-square w-full" : "space-x-3 w-full"
                )}
                title="Share & gift"
            >
                <div className={cn("flex items-center justify-center shrink-0 w-8 h-8", isCollapsed ? "" : "w-8")}>
                    <lord-icon
                        src="/lordicon/gift.json"
                        trigger="hover"
                        style={{ width: 22, height: 22 }}
                        colors="primary:#d1d5db,secondary:#ffffff"
                    />
                </div>
                {!isCollapsed && (
                    <span className="text-xs font-semibold">Share & gift</span>
                )}
            </button>

            {/* Bug Report Button - Placed above the user profile */}
            <button
                onClick={() => setIsFeedbackOpen(true)}
                className={cn(
                    "flex items-center rounded-xl hover:bg-white/5 cursor-pointer group transition-all text-gray-400 hover:text-orange-400 p-2 border border-transparent hover:border-white/5",
                    isCollapsed ? "justify-center aspect-square w-full" : "space-x-3 w-full"
                )}
                title="Report a bug"
            >
                <div className={cn("flex items-center justify-center shrink-0 w-8 h-8", isCollapsed ? "" : "w-8")}>
                    <lord-icon
                        src="/lordicon/bug.json"
                        trigger="hover"
                        style={{ width: 22, height: 22 }}
                        colors="primary:#9ca3af,secondary:#fb923c"
                    />
                </div>
                {!isCollapsed && (
                    <span className="text-xs font-semibold">Report a bug</span>
                )}
            </button>

            <div
                onClick={() => router.push('/app/profile')}
                className={cn(
                    "flex items-center p-2 rounded-xl hover:bg-white/5 cursor-pointer group transition-all",
                    isCollapsed ? "justify-center" : "space-x-3"
                )}
            >
                {/* User Avatar */}
                <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs text-primary font-bold shrink-0">
                    {user?.email?.[0].toUpperCase() || "U"}
                </div>

                {/* Expanded View */}
                {!isCollapsed && (
                    <>
                        <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-gray-200 truncate">
                                {user?.displayName || user?.email?.split('@')[0] || "User"}
                            </p>
                            <p className="text-[9px] font-bold text-gray-500 uppercase tracking-tighter">
                                {planDisplayName}
                            </p>
                        </div>

                        <LogoutButton className="glass-button-red w-8 h-8 p-0 shrink-0 group/logout">
                            <LogoutIcon size={16} />
                        </LogoutButton>
                    </>
                )}
            </div>

            <FeedbackModal
                isOpen={isFeedbackOpen}
                onClose={() => setIsFeedbackOpen(false)}
            />
            <GiftShareModal
                isOpen={isGiftOpen}
                onClose={() => setIsGiftOpen(false)}
            />
        </div>
    );
};
