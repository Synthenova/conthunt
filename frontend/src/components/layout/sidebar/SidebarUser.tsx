"use client";

import React, { useState } from 'react';
import { LogoutIcon, type LogoutIconHandle } from '@/components/ui/logout';
import { cn } from '@/lib/utils';
import { LogoutButton } from "@/components/logout-button";
import { useRouter } from 'next/navigation';
import { useProducts } from '@/contexts/ProductsContext';
import { Bug, Gift } from 'lucide-react';
import { FeedbackModal } from '@/components/modals/FeedbackModal';
import { GiftShareModal } from '@/components/modals/GiftShareModal';

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

    const planDisplayName = profile?.role
        ? getPlanName(profile.role)
        : (productsLoading ? "Loading..." : "Free");

    return (
        <div className="p-4 border-t border-white/5 mt-auto space-y-2">
            <button
                onClick={() => setIsGiftOpen(true)}
                className={cn(
                    "flex items-center rounded-xl hover:bg-white/5 cursor-pointer group transition-all text-gray-300 hover:text-emerald-400 p-2 border border-transparent hover:border-white/5",
                    isCollapsed ? "justify-center aspect-square w-full" : "space-x-3 w-full"
                )}
                title="Share & gift"
            >
                <div className={cn("flex items-center justify-center", isCollapsed ? "" : "w-8")}>
                    <Gift size={16} />
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
                <div className={cn("flex items-center justify-center", isCollapsed ? "" : "w-8")}>
                    <Bug size={16} />
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
