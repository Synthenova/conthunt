"use client";

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutGrid,
    Search,
    LogOut,
    ChevronRight,
    ChevronLeft,
    MessageSquare,
    Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSearch } from "@/hooks/useSearch";
import { useBoards } from "@/hooks/useBoards";
import { useChatList } from "@/hooks/useChat";
import { useChatStore } from "@/lib/chatStore";
import { LogoutButton } from "@/components/logout-button";
import { StaggerContainer, StaggerItem, AnimatePresence } from "@/components/ui/animations";
import { useUser } from "@/hooks/useUser";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { motion } from "framer-motion";
import { SearchIcon } from "@/components/ui/search";
import { HistoryIcon } from "@/components/ui/history";
import { LayoutPanelTopIcon } from "@/components/ui/layout-panel-top";

const navItems = [
    { title: "Search", path: "/app", icon: SearchIcon },
    { title: "Chats", path: "/app/chats", icon: HistoryIcon },
    { title: "Boards", path: "/app/boards", icon: LayoutPanelTopIcon },
];

const NavItem = ({ icon: Icon, label, path, active, isCollapsed, onModalClick }: any) => {
    const isModalNav = label === 'Chats' || label === 'Searches';
    const iconRef = React.useRef<any>(null);

    const handleMouseEnter = () => {
        iconRef.current?.startAnimation?.();
    };

    const handleMouseLeave = () => {
        iconRef.current?.stopAnimation?.();
    };

    const content = (
        <>
            <div className="relative z-10 flex items-center gap-3">
                <Icon
                    ref={iconRef}
                    size={20}
                    className={cn("transition-colors shrink-0", active ? "text-white" : "group-hover:text-gray-200")}
                />
                {!isCollapsed && (
                    <span className="font-medium text-sm whitespace-nowrap overflow-hidden transition-all duration-300 origin-left">
                        {label}
                    </span>
                )}
            </div>
            {active && (
                <motion.div
                    layoutId="nav-pill"
                    className="absolute inset-0 rounded-full glass-pill"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
            )}
        </>
    );

    const classes = cn(
        "flex items-center transition-all duration-200 group relative",
        isCollapsed
            ? "justify-center w-12 h-12 rounded-full mx-auto"
            : "w-full space-x-3 px-3 py-2.5 rounded-full",
        active
            ? "text-white"
            : "text-gray-400 hover:text-gray-200"
    );

    if (isModalNav) {
        return (
            <button
                type="button"
                onClick={onModalClick}
                className={classes}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
            >
                {content}
            </button>
        );
    }

    return (
        <Link
            href={path}
            className={classes}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            {content}
        </Link>
    );
};

const RecentsItem = ({ label, icon: Icon, active, onClick, href }: any) => {
    const content = (
        <>
            <div className="relative z-10 flex items-center gap-3">
                {Icon && <Icon size={16} className={cn("shrink-0 transition-colors opacity-70", active ? "text-white opacity-100" : "group-hover:text-gray-200 group-hover:opacity-100")} />}
                <span className={cn("text-sm truncate font-medium transition-colors", active ? "text-white" : "text-gray-400 group-hover:text-gray-200")}>
                    {label}
                </span>
            </div>
            {active && (
                <motion.div
                    layoutId="recent-item-pill"
                    className="absolute inset-0 rounded-lg bg-white/5 border border-white/5 shadow-sm"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
            )}
        </>
    );

    const containerClasses = cn(
        "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left group relative"
    );

    if (onClick) {
        return (
            <button onClick={onClick} className={containerClasses}>
                {content}
            </button>
        );
    }

    return (
        <Link href={href} className={containerClasses}>
            {content}
        </Link>
    );
};

import { useMediaQuery } from "@/hooks/use-media-query";
import { PanelLeft, PanelLeftClose, Menu } from 'lucide-react';

// ... (other imports remain, remove ChevronRight/Left if unused)

export function AppSidebar({
    collapsed,
    forcedCollapsed = false,
    overlay = false,
    onCollapsedChange,
}: {
    collapsed?: boolean;
    forcedCollapsed?: boolean;
    overlay?: boolean;
    onCollapsedChange?: (next: boolean) => void;
} = {}) {
    const pathname = usePathname();
    const router = useRouter();
    const isDesktop = useMediaQuery("(min-width: 768px)");

    // Desktop: collapse state. Mobile: open state (overlay).
    const [internalCollapsed, setInternalCollapsed] = useState(false);
    const isCollapsed = collapsed ?? internalCollapsed;
    const setCollapsed = (next: boolean) => {
        if (onCollapsedChange) {
            onCollapsedChange(next);
            return;
        }
        setInternalCollapsed(next);
    };
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    const [activeTab, setActiveTab] = useState<'boards' | 'chats' | 'searches'>('chats');
    const [isRecentsModalOpen, setIsRecentsModalOpen] = useState(false);
    const [recentsModalTab, setRecentsModalTab] = useState<'chats' | 'searches'>('chats');

    const { openSidebar, setActiveChatId } = useChatStore();
    const { history, isLoadingHistory } = useSearch();
    const { boards, isLoadingBoards } = useBoards();
    const { data: allChats = [], isLoading: isLoadingChats } = useChatList(undefined, { setStore: false });
    const { user, profile } = useUser();

    // Reset mobile state on path change
    React.useEffect(() => {
        setIsMobileOpen(false);
    }, [pathname]);

    // ... (rest of state and hooks)

    // Helper to group chats by date
    const groupChatsByDate = (chats: any[]) => {
        const groups: Record<string, any[]> = {
            "Today": [],
            "Yesterday": [],
            "Previous 7 Days": [],
            "Previous 30 Days": [],
            "Older": []
        };

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const last7Days = new Date(today);
        last7Days.setDate(last7Days.getDate() - 7);
        const last30Days = new Date(today);
        last30Days.setDate(last30Days.getDate() - 30);

        chats.forEach(chat => {
            const date = new Date(chat.updated_at);
            if (date >= today) {
                groups["Today"].push(chat);
            } else if (date >= yesterday) {
                groups["Yesterday"].push(chat);
            } else if (date >= last7Days) {
                groups["Previous 7 Days"].push(chat);
            } else if (date >= last30Days) {
                groups["Previous 30 Days"].push(chat);
            } else {
                groups["Older"].push(chat);
            }
        });

        return groups;
    };

    const sortedAllChats = useMemo(() => {
        return [...allChats].sort((a, b) => {
            const aTime = new Date(a.updated_at).getTime();
            const bTime = new Date(b.updated_at).getTime();
            return bTime - aTime;
        });
    }, [allChats]);

    // Group only the top 12 for sidebar to avoid clutter, or maybe just group the sorted list
    // For sidebar we just take top N then group them, OR group all and show limited? 
    // Usually sidebar shows "Recent" which implies time sorted. 
    // Let's group the `sortedChats` (top 10) for sidebar.
    const sortedChats = useMemo(() => sortedAllChats.slice(0, 20), [sortedAllChats]); // Increased slice for grouping context
    const groupedSidebarChats = useMemo(() => groupChatsByDate(sortedChats), [sortedChats]);
    const groupedAllChats = useMemo(() => groupChatsByDate(sortedAllChats), [sortedAllChats]);

    const activeListCount = activeTab === 'chats'
        ? sortedChats.length
        : activeTab === 'boards'
            ? boards.length
            : history.length;

    const handleOpenChat = (chatId: string) => {
        const targetPath = `/app/chats/${chatId}`;
        setActiveChatId(chatId);
        openSidebar();
        if (pathname !== targetPath) {
            router.push(targetPath);
        }
    };

    const isActive = (path: string) => {
        if (path === '/app' && pathname === '/app') return true;
        if (path !== '/app' && pathname.startsWith(path)) return true;
        return false;
    };

    const isRecentActive = (type: 'chats' | 'boards' | 'searches', id: string) => {
        return pathname === `/app/${type}/${id}`;
    };

    const openRecentsModal = (tab: 'chats' | 'searches') => {
        setRecentsModalTab(tab);
        setIsRecentsModalOpen(true);
    };

    const handleNavClick = (label: string, path: string) => {
        if (label === 'Chats') {
            openRecentsModal('chats');
            return;
        }
        if (label === 'Searches') {
            openRecentsModal('searches');
            return;
        }
        router.push(path);
    };

    const roleLabels: Record<string, string> = {
        free: "Free Plan",
        creator: "Creator Plan",
        pro_research: "Pro Research"
    };

    // Mobile View (Rendered conditionally after all hooks)
    if (!isDesktop) {
        return (
            <>
                {/* Mobile Toggle Button */}
                <button
                    onClick={() => setIsMobileOpen(true)}
                    className="fixed top-4 right-4 z-50 p-2 bg-[#0B0E13] border border-white/10 rounded-full text-white shadow-lg"
                >
                    <Menu size={20} />
                </button>

                {/* Mobile Overlay Sidebar */}
                <AnimatePresence>
                    {isMobileOpen && (
                        <>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setIsMobileOpen(false)}
                                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
                            />
                            <motion.aside
                                initial={{ x: "-100%" }}
                                animate={{ x: 0 }}
                                exit={{ x: "-100%" }}
                                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                                className="fixed inset-y-0 left-0 z-50 w-[280px] bg-[#030303] border-r border-white/10 flex flex-col font-main"
                            >
                                {/* Mobile Header */}
                                <div className="flex items-center justify-between h-[72px] px-5 border-b border-white/5">
                                    <div className="flex items-center space-x-3 text-white">
                                        <div className="w-8 h-8 rounded-lg bg-surface border border-white/10 flex items-center justify-center shrink-0">
                                            <span className="font-bold text-lg text-primary">C</span>
                                        </div>
                                        <span className="font-semibold text-lg tracking-tight">Conthunt</span>
                                    </div>
                                    <button onClick={() => setIsMobileOpen(false)} className="text-gray-400 hover:text-white">
                                        <PanelLeftClose size={20} />
                                    </button>
                                </div>

                                {/* Scrollable Content */}
                                <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                                    <div className="px-3 space-y-1 mt-4">
                                        {navItems.map(item => (
                                            <NavItem
                                                key={item.path}
                                                {...item}
                                                label={item.title}
                                                active={isActive(item.path)}
                                                isCollapsed={false}
                                                onModalClick={() => handleNavClick(item.title, item.path)}
                                            />
                                        ))}
                                    </div>
                                    {/* Mobile Recents (Always Expanded) */}
                                    <div className="mt-8 flex-1 flex flex-col min-h-0 px-4">
                                        <div className="flex items-center justify-between mb-4">
                                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Recents</span>
                                        </div>
                                        <div className="flex p-1 bg-white/5 glass-nav rounded-full relative mb-4 h-12 items-center">
                                            {(['boards', 'chats'] as const).map((tab) => (
                                                <button
                                                    key={tab}
                                                    onClick={() => setActiveTab(tab)}
                                                    className={cn(
                                                        "flex-1 h-full flex items-center justify-center text-xs font-bold uppercase tracking-wider rounded-full transition-all relative z-10",
                                                        activeTab === tab ? "text-white" : "text-gray-500 hover:text-gray-300"
                                                    )}
                                                >
                                                    {activeTab === tab && (
                                                        <motion.div
                                                            layoutId="mobile-recents-tab-pill" // Distinct ID for mobile
                                                            className="absolute inset-0 rounded-full glass-pill"
                                                            style={{ borderRadius: 9999 }}
                                                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                                        />
                                                    )}
                                                    <span className="relative z-10 mix-blend-normal">{tab}</span>
                                                </button>
                                            ))}
                                        </div>
                                        <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
                                            {/* Reuse list logic - duplicated for simplicity in this step */}
                                            {activeTab === 'chats' && (
                                                isLoadingChats ? (
                                                    <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-gray-600" /></div>
                                                ) : sortedChats.length > 0 ? (
                                                    sortedChats.map((chat: any) => (
                                                        <RecentsItem
                                                            key={chat.id}
                                                            label={chat.title || "New Chat"}
                                                            icon={MessageSquare}
                                                            active={isRecentActive('chats', chat.id)}
                                                            onClick={() => {
                                                                handleOpenChat(chat.id);
                                                                setIsMobileOpen(false);
                                                            }}
                                                        />
                                                    ))
                                                ) : (
                                                    <div className="px-3 py-8 text-[10px] text-gray-500 text-center border border-dashed border-white/5 rounded-xl">No active chats</div>
                                                )
                                            )}
                                            {activeTab === 'boards' && (
                                                isLoadingBoards ? (
                                                    <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-gray-600" /></div>
                                                ) : boards.length > 0 ? (
                                                    boards.slice(0, 10).map((board: any) => (
                                                        <RecentsItem
                                                            key={board.id}
                                                            label={board.name}
                                                            icon={LayoutGrid}
                                                            active={isRecentActive('boards', board.id)}
                                                            href={`/app/boards/${board.id}`}
                                                            onClick={() => setIsMobileOpen(false)} // Auto close on mobile nav
                                                        />
                                                    ))
                                                ) : (
                                                    <div className="px-3 py-8 text-[10px] text-gray-500 text-center border border-dashed border-white/5 rounded-xl">No boards created</div>
                                                )
                                            )}
                                            <button
                                                onClick={() => {
                                                    if (activeTab === 'boards') {
                                                        router.push('/app/boards');
                                                        setIsMobileOpen(false);
                                                        return;
                                                    }
                                                    openRecentsModal(activeTab === 'chats' ? 'chats' : 'searches');
                                                }}
                                                className="mt-2 text-[10px] font-bold text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
                                            >
                                                View all <ChevronRight size={10} />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Footer */}
                                    <div className="p-4 border-t border-white/5 mt-auto">
                                        <div className="flex items-center space-x-3 p-2 rounded-xl bg-white/5">
                                            <div className="w-8 h-8 rounded-full bg-surface border border-white/10 flex items-center justify-center text-xs text-primary font-bold shrink-0">
                                                {user?.email?.[0].toUpperCase() || "U"}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-xs font-semibold text-gray-200 truncate">
                                                    {user?.displayName || user?.email?.split('@')[0] || "User"}
                                                </p>
                                                <p className="text-[9px] font-bold text-gray-500 uppercase tracking-tighter">
                                                    {profile?.role ? roleLabels[profile.role] : "Loading..."}
                                                </p>
                                            </div>
                                            <LogoutButton className="p-0 border-0 bg-transparent hover:bg-transparent shadow-none text-gray-500 hover:text-red-400 transition-colors">
                                                <LogOut size={16} />
                                            </LogoutButton>
                                        </div>
                                    </div>
                                </div>
                            </motion.aside>
                        </>
                    )}
                </AnimatePresence>
            </>
        );
    }

    // Desktop View
    return (
        <aside className={cn(
            "bg-background border-r border-white/5 flex flex-col transition-all duration-300 ease-in-out font-main",
            overlay ? "fixed inset-y-0 left-0 z-50 shadow-2xl" : "relative z-40 h-full",
            isCollapsed ? "w-20" : "w-[280px]"
        )}>
            {/* Header with Integrated Toggle */}
            <div className={cn("flex items-center h-[72px] transition-all", isCollapsed ? "justify-center" : "px-5 justify-between")}>
                {!isCollapsed ? (
                    <>
                        <div className="flex items-center space-x-3 text-white overflow-hidden">
                            <div className="w-8 h-8 rounded-lg bg-surface border border-white/10 flex items-center justify-center shrink-0">
                                <span className="font-bold text-lg text-primary">C</span>
                            </div>
                            <span className="font-semibold text-lg tracking-tight whitespace-nowrap animate-in fade-in duration-300">
                                Conthunt
                            </span>
                        </div>
                        <button
                            onClick={() => setCollapsed(true)}
                            className="text-gray-500 hover:text-white transition-colors"
                        >
                            <PanelLeftClose size={20} />
                        </button>
                    </>
                ) : (
                    <button
                        onClick={() => {
                            setCollapsed(false);
                        }}
                        className="w-10 h-10 rounded-xl bg-surface border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:scale-105 transition-all shadow-sm"
                    >
                        <PanelLeft size={20} />
                    </button>
                )}
            </div>

            {/* Main Nav */}
            <div className="px-3 space-y-1">
                {navItems.map(item => (
                    <NavItem
                        key={item.path}
                        {...item}
                        label={item.title}
                        active={isActive(item.path)}
                        isCollapsed={isCollapsed}
                        onModalClick={() => handleNavClick(item.title, item.path)}
                    />
                ))}
            </div>

            {/* Recents Section */}
            <div className={cn(
                "mt-8 flex-1 flex flex-col min-h-0 transition-opacity duration-200",
                isCollapsed ? "opacity-0 invisible px-0" : "opacity-100 visible px-4"
            )}>
                {!isCollapsed && (
                    <>
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Recents</span>
                        </div>

                        {/* Tabs */}
                        <div className="flex p-1 bg-white/5 glass-nav rounded-full relative mb-4 h-12 items-center">
                            {(['boards', 'chats'] as const).map((tab) => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={cn(
                                        "flex-1 h-full flex items-center justify-center text-xs font-bold uppercase tracking-wider rounded-full transition-all relative z-10",
                                        activeTab === tab
                                            ? "text-white"
                                            : "text-gray-500 hover:text-gray-300"
                                    )}
                                >
                                    {activeTab === tab && (
                                        <motion.div
                                            layoutId="recents-tab-pill"
                                            className="absolute inset-0 rounded-full glass-pill"
                                            style={{ borderRadius: 9999 }} // Force full rounded for tabs
                                            transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                        />
                                    )}
                                    <span className="relative z-10 mix-blend-normal">{tab}</span>
                                </button>
                            ))}
                        </div>

                        {/* List Content */}
                        <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
                            <AnimatePresence mode="wait">
                                <StaggerContainer
                                    key={`${activeTab}-${activeListCount}`}
                                    className="space-y-1"
                                    initial={false}
                                >
                                    {activeTab === 'chats' && (
                                        isLoadingChats ? (
                                            <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-gray-600" /></div>
                                        ) : sortedChats.length > 0 ? (
                                            Object.entries(groupedSidebarChats).map(([group, chats]) => (
                                                chats.length > 0 && (
                                                    <div key={group} className="mb-4">
                                                        <div className="px-2 mb-2 text-[10px] font-semibold text-gray-600 uppercase tracking-wider">{group}</div>
                                                        <div className="space-y-0.5">
                                                            {chats.map((chat: any) => (
                                                                <StaggerItem key={chat.id}>
                                                                    <RecentsItem
                                                                        label={chat.title || "New Chat"}
                                                                        // No icon for sidebar as requested
                                                                        active={isRecentActive('chats', chat.id)}
                                                                        onClick={() => handleOpenChat(chat.id)}
                                                                    />
                                                                </StaggerItem>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )
                                            ))
                                        ) : (
                                            <div className="px-3 py-8 text-[10px] text-gray-500 text-center border border-dashed border-white/5 rounded-xl">No active chats</div>
                                        )
                                    )}

                                    {activeTab === 'boards' && (
                                        isLoadingBoards ? (
                                            <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-gray-600" /></div>
                                        ) : boards.length > 0 ? (
                                            boards.slice(0, 10).map((board: any) => (
                                                <StaggerItem key={board.id}>
                                                    <RecentsItem
                                                        label={board.name}
                                                        icon={LayoutGrid}
                                                        active={isRecentActive('boards', board.id)}
                                                        href={`/app/boards/${board.id}`}
                                                    />
                                                </StaggerItem>
                                            ))
                                        ) : (
                                            <div className="px-3 py-8 text-[10px] text-gray-500 text-center border border-dashed border-white/5 rounded-xl">No boards created</div>
                                        )
                                    )}

                                    {/* {activeTab === 'searches' && (
                                        isLoadingHistory ? (
                                            <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-gray-600" /></div>
                                        ) : history.length > 0 ? (
                                            history.slice(0, 10).map((item: any) => (
                                                <StaggerItem key={item.id}>
                                                    <Link
                                                        href={`/app/searches/${item.id}`}
                                                        className={cn(
                                                            "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all group",
                                                            isRecentActive('searches', item.id)
                                                                ? "bg-white/10 text-white"
                                                                : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                                                        )}
                                                    >
                                                        <Search size={14} className="shrink-0 opacity-50 group-hover:opacity-100" />
                                                        <span className="text-xs truncate font-medium">{item.query}</span>
                                                    </Link>
                                                </StaggerItem>
                                            ))
                                        ) : (
                                            <div className="px-3 py-8 text-[10px] text-gray-500 text-center border border-dashed border-white/5 rounded-xl">No search history</div>
                                        )
                                    )} */}
                                    <button
                                        onClick={() => {
                                            if (activeTab === 'boards') {
                                                router.push('/app/boards');
                                                return;
                                            }
                                            openRecentsModal(activeTab === 'chats' ? 'chats' : 'searches');
                                        }}
                                        className="mt-2 text-[10px] font-bold text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
                                    >
                                        View all <ChevronRight size={10} />
                                    </button>
                                </StaggerContainer>
                            </AnimatePresence>
                        </div>
                    </>
                )}
            </div>

            {/* Footer */}
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
            <Dialog open={isRecentsModalOpen} onOpenChange={setIsRecentsModalOpen}>
                <DialogContent className="bg-[#1C1C1C] border border-white/5 text-gray-200 max-w-lg p-0 gap-0 overflow-hidden shadow-2xl rounded-2xl">
                    <div className="p-4 border-b border-white/5 flex items-center gap-3">
                        <Search size={16} className="text-gray-500" />
                        <input
                            className="bg-transparent border-none outline-none text-sm placeholder:text-gray-500 flex-1 text-white"
                            placeholder="Search chats..."
                            autoFocus
                        />
                    </div>
                    <div className="p-2 space-y-1">
                        <button
                            onClick={() => {
                                // Logic to create new chat would go here
                                setIsRecentsModalOpen(false);
                                router.push('/app'); // Assuming /app is new chat
                            }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white hover:bg-white/5 transition-all text-left font-medium text-sm group"
                        >
                            <MessageSquare size={16} className="shrink-0 text-white" />
                            New chat
                        </button>
                    </div>

                    <div className="max-h-[60vh] overflow-y-auto px-2 pb-4 custom-scrollbar">
                        {recentsModalTab === 'chats' ? (
                            isLoadingChats ? (
                                <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-gray-500" /></div>
                            ) : sortedAllChats.length > 0 ? (
                                Object.entries(groupedAllChats).map(([group, chats]) => (
                                    chats.length > 0 && (
                                        <div key={group} className="mt-4 first:mt-2">
                                            <div className="px-3 mb-2 text-[11px] font-medium text-gray-500">{group}</div>
                                            <div className="space-y-0.5">
                                                {chats.map((chat: any) => (
                                                    <button
                                                        key={chat.id}
                                                        onClick={() => {
                                                            handleOpenChat(chat.id);
                                                            setIsRecentsModalOpen(false);
                                                        }}
                                                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all text-left group"
                                                    >
                                                        <MessageSquare size={16} className="shrink-0 opacity-70 group-hover:opacity-100 transition-opacity" />
                                                        <span className="text-sm truncate">{chat.title || "New Chat"}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )
                                ))
                            ) : (
                                <div className="px-3 py-8 text-xs text-gray-500 text-center">
                                    No active chats
                                </div>
                            )
                        ) : null}
                        {/* Searches modal list hidden for now. */}
                    </div>
                </DialogContent>
            </Dialog>
        </aside>
    );
}
