"use client";

import React from 'react';
import { LogoutIcon, type LogoutIconHandle } from '@/components/ui/logout';
import { cn } from '@/lib/utils';
import { LogoutButton } from "@/components/logout-button";
import { useRouter } from 'next/navigation';
import { useProducts } from '@/contexts/ProductsContext';

interface SidebarUserProps {
    user: any;
    profile: any;
    isCollapsed: boolean;
}

export const SidebarUser = ({ user, profile, isCollapsed }: SidebarUserProps) => {
    const router = useRouter();
    const { getPlanName, loading: productsLoading } = useProducts();

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
        </div>
    );
};
