"use client";

import React from 'react';
import { LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { LogoutButton } from "@/components/logout-button";
import { useRouter } from 'next/navigation';

interface SidebarUserProps {
    user: any;
    profile: any;
    isCollapsed: boolean;
}

const roleLabels: Record<string, string> = {
    free: "Free Plan",
    creator: "Creator Plan",
    pro_research: "Pro Research"
};

export const SidebarUser = ({ user, profile, isCollapsed }: SidebarUserProps) => {
    const router = useRouter();

    return (
        <div className="p-4 border-t border-white/5 mt-auto">
            <div
                onClick={() => router.push('/app/profile')}
                className={cn(
                    "flex items-center p-2 rounded-xl hover:bg-white/5 cursor-pointer group transition-all",
                    isCollapsed ? "justify-center" : "space-x-3"
                )}
            >
                <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs text-primary font-bold shrink-0">
                    {user?.email?.[0].toUpperCase() || "U"}
                </div>
                {!isCollapsed && (
                    <>
                        <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-gray-200 truncate">
                                {user?.displayName || user?.email?.split('@')[0] || "User"}
                            </p>
                            <p className="text-[9px] font-bold text-gray-500 uppercase tracking-tighter">
                                {profile?.role ? roleLabels[profile.role] : "Loading plan..."}
                            </p>
                        </div>
                        <LogoutButton className="p-0 border-0 bg-transparent hover:bg-transparent shadow-none text-gray-500 hover:text-red-400 transition-colors">
                            <LogOut size={16} />
                        </LogoutButton>
                    </>
                )}
            </div>
        </div>
    );
};
