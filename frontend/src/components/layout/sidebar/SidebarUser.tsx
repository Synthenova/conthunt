"use client";

import React from 'react';
import { LogoutIcon, type LogoutIconHandle } from '@/components/ui/logout';
import { cn } from '@/lib/utils';
import { LogoutButton } from "@/components/logout-button";
import { useRouter } from 'next/navigation';
import { useProducts } from '@/contexts/ProductsContext';
import { useStreak } from '@/hooks/useStreak';
import { Flame } from 'lucide-react';

interface SidebarUserProps {
    user: any;
    profile: any;
    isCollapsed: boolean;
}

export const SidebarUser = ({ user, profile, isCollapsed }: SidebarUserProps) => {
    const router = useRouter();
    const { getPlanName, loading: productsLoading } = useProducts();
    const { streak: streakData } = useStreak();

    const planDisplayName = profile?.role
        ? getPlanName(profile.role)
        : (productsLoading ? "Loading..." : "Free");

    return (
        <div className="p-4 border-t border-white/5 mt-auto">
            <div
                onClick={() => router.push('/app/profile')}
                className={cn(
                    "flex items-center p-2 rounded-xl hover:bg-white/5 cursor-pointer group transition-all",
                    isCollapsed ? "justify-center" : "space-x-3"
                )}
            >
                {/* Streak Icon - Collapsed View */}
                {isCollapsed && streakData && streakData.current_streak > 0 && (
                    <div className="relative">
                        <Flame className="h-5 w-5 text-orange-400" />
                        <span className="absolute -top-1 -right-1 text-[8px] font-bold text-orange-400">
                            {streakData.current_streak}
                        </span>
                    </div>
                )}

                {/* User Avatar - Collapsed shows avatar if no streak */}
                {(isCollapsed && (!streakData || streakData.current_streak === 0)) && (
                    <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs text-primary font-bold shrink-0">
                        {user?.email?.[0].toUpperCase() || "U"}
                    </div>
                )}

                {/* Expanded View */}
                {!isCollapsed && (
                    <>
                        <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs text-primary font-bold shrink-0">
                            {user?.email?.[0].toUpperCase() || "U"}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-gray-200 truncate">
                                {user?.displayName || user?.email?.split('@')[0] || "User"}
                            </p>
                            <p className="text-[9px] font-bold text-gray-500 uppercase tracking-tighter">
                                {planDisplayName}
                            </p>
                        </div>

                        {/* Streak Badge */}
                        {streakData && streakData.current_streak > 0 && (
                            <div className="flex items-center gap-1 px-2 py-1 bg-orange-500/10 border border-orange-500/20 rounded-full shrink-0">
                                <Flame className="h-3 w-3 text-orange-400" />
                                <span className="text-[10px] font-bold text-orange-400">
                                    {streakData.current_streak}
                                </span>
                            </div>
                        )}

                        <LogoutButton className="glass-button-red w-8 h-8 p-0 shrink-0 group/logout">
                            <LogoutIcon size={16} />
                        </LogoutButton>
                    </>
                )}
            </div>
        </div>
    );
};
