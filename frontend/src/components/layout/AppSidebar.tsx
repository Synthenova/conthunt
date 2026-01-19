"use client";

import React, { useMemo, useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutGrid,
    Search,
    PanelLeft,
    PanelLeftClose,
    Menu,
    Loader2,
    MessageSquare,
    ChevronRight,
    ChevronLeft,
    LayoutPanelTop,
    Pencil,
    Trash,
    Flame
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSearch } from "@/hooks/useSearch";
import { useBoards } from "@/hooks/useBoards";
import { useChatList, useRenameChat, useDeleteChat } from "@/hooks/useChat";
import { useChatStore } from "@/lib/chatStore";
import { StaggerContainer, StaggerItem, AnimatePresence } from "@/components/ui/animations";
import { useUser } from "@/hooks/useUser";
import { useMediaQuery } from "@/hooks/use-media-query";
import { useStreak } from "@/hooks/useStreak";
import { motion } from "framer-motion";

// Animated icons
import { HomeIcon } from "@/components/ui/home";
import { HistoryIcon } from "@/components/ui/history";
import { LayoutPanelTopIcon } from "@/components/ui/layout-panel-top";

// Extracted Components
import { NavItem } from "@/components/layout/sidebar/NavItem";
import { RecentsItem } from "@/components/layout/sidebar/RecentsItem";
import { SidebarUser } from "@/components/layout/sidebar/SidebarUser";
import { SidebarRecentsModal } from "@/components/layout/sidebar/SidebarRecentsModal";

const navItems = [
    { title: "Home", path: "/app", icon: HomeIcon },
    { title: "Chats", path: "/app/chats", icon: HistoryIcon },
    { title: "Boards", path: "/app/boards", icon: LayoutPanelTopIcon },
];

const SidebarLogo = () => (
    <div className="flex items-center text-white overflow-hidden">
        <Image
            src="/images/logo-title-white.png"
            alt="Conthunt"
            width={120}
            height={33}
            priority
            className="w-32 h-auto object-contain"
        />
    </div>
);

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
    const [editingChatId, setEditingChatId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');
    const editInputRef = useRef<HTMLInputElement | null>(null);
    const [hoveredChatId, setHoveredChatId] = useState<string | null>(null);

    const { openSidebar, setActiveChatId } = useChatStore();
    const { history, isLoadingHistory } = useSearch();
    const { boards, isLoadingBoards } = useBoards();
    const { data: allChats = [], isLoading: isLoadingChats } = useChatList(undefined, { setStore: false });
    const renameChat = useRenameChat();
    const deleteChat = useDeleteChat();
    const { user, profile } = useUser();
    const { streak: streakData } = useStreak();

    // Reset mobile state on path change
    useEffect(() => {
        setIsMobileOpen(false);
    }, [pathname]);

    useEffect(() => {
        if (editingChatId) {
            editInputRef.current?.focus();
            editInputRef.current?.select();
        }
    }, [editingChatId]);

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

    const sortedChats = useMemo(() => sortedAllChats.slice(0, 20), [sortedAllChats]);
    const groupedSidebarChats = useMemo(() => groupChatsByDate(sortedChats), [sortedChats]);
    const groupedAllChats = useMemo(() => groupChatsByDate(sortedAllChats), [sortedAllChats]);

    const activeListCount = activeTab === 'chats'
        ? sortedChats.length
        : activeTab === 'boards'
            ? boards.length
            : history.length;

    const handleOpenChat = (chat: any) => {
        if (editingChatId) return;

        if (chat.context_id && chat.context_type === 'board') {
            router.push(`/app/boards/${chat.context_id}`);
            return;
        }

        const targetPath = `/app/chats/${chat.id}`;
        setActiveChatId(chat.id);
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

    const startChatEdit = (chatId: string, title?: string) => {
        setEditingChatId(chatId);
        setEditingTitle(title || '');
    };

    const cancelChatEdit = () => {
        setEditingChatId(null);
        setEditingTitle('');
    };

    const commitChatEdit = async () => {
        if (!editingChatId) return;
        const nextTitle = editingTitle.trim();
        const targetChatId = editingChatId;
        cancelChatEdit();
        if (!nextTitle) return;
        try {
            await renameChat.mutateAsync({ chatId: targetChatId, title: nextTitle });
        } catch (err) {
            console.error(err);
        }
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

    const renderChatItem = (chat: any, options?: { showIcon?: boolean; onSelect?: () => void }) => {
        const isEditing = editingChatId === chat.id;
        const isActiveChat = isRecentActive('chats', chat.id);

        return (
            <div
                key={chat.id}
                role="button"
                tabIndex={0}
                onClick={() => {
                    if (isEditing) return;
                    handleOpenChat(chat);
                    options?.onSelect?.();
                }}
                onKeyDown={(event) => {
                    if (isEditing) return;
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        handleOpenChat(chat);
                        options?.onSelect?.();
                    }
                }}
                onMouseEnter={() => setHoveredChatId(chat.id)}
                onMouseLeave={() => setHoveredChatId((prev) => (prev === chat.id ? null : prev))}
                className={cn(
                    "w-full flex items-center gap-2 px-3 py-2.5 rounded-lg transition-all text-left group relative overflow-hidden",
                    isEditing
                        ? "cursor-text border border-white/15 bg-transparent"
                        : "cursor-pointer"
                )}
            >
                <div className="relative z-10 flex items-center gap-1.5 min-w-0 flex-1 pr-0">
                    {options?.showIcon && (
                        <MessageSquare
                            size={16}
                            className={cn(
                                "shrink-0 transition-colors opacity-70",
                                isActiveChat ? "text-white opacity-100" : "group-hover:text-gray-200 group-hover:opacity-100"
                            )}
                        />
                    )}
                    {isEditing ? (
                        <input
                            ref={editInputRef}
                            value={editingTitle}
                            onChange={(event) => setEditingTitle(event.target.value)}
                            onKeyDown={(event) => {
                                if (event.key === 'Enter') {
                                    event.preventDefault();
                                    commitChatEdit();
                                }
                                if (event.key === 'Escape') {
                                    event.preventDefault();
                                    cancelChatEdit();
                                }
                            }}
                            onBlur={cancelChatEdit}
                            className="w-full bg-transparent text-sm font-medium text-white placeholder:text-gray-500 outline-none"
                        />
                    ) : (
                        <span
                            className={cn(
                                "text-sm font-medium transition-colors block w-full overflow-hidden",
                                isActiveChat ? "text-white" : "text-gray-400 group-hover:text-gray-200"
                            )}
                            style={{
                                maxWidth: hoveredChatId === chat.id ? "calc(100% - 35px)" : "100%",
                                maskImage: hoveredChatId === chat.id
                                    ? "linear-gradient(to right, #fff 97%, transparent)"
                                    : "linear-gradient(to right, #fff 99%, transparent)",
                                WebkitMaskImage: hoveredChatId === chat.id
                                    ? "linear-gradient(to right, #fff 97%, transparent)"
                                    : "linear-gradient(to right, #fff 99%, transparent)",
                                transition: "max-width 0.15s ease, mask-image 0.15s ease, -webkit-mask-image 0.15s ease",
                            }}
                            title={chat.title || "New Chat"}
                        >
                            <span className="whitespace-nowrap block">
                                {chat.title || "New Chat"}
                            </span>
                        </span>
                    )}
                </div>
                {!isEditing && (
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 z-20 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                            type="button"
                            onClick={(event) => {
                                event.stopPropagation();
                                startChatEdit(chat.id, chat.title);
                            }}
                            className="text-gray-400 hover:text-gray-200"
                            aria-label="Rename chat"
                        >
                            <Pencil size={14} />
                        </button>
                        <button
                            type="button"
                            onClick={(event) => {
                                event.stopPropagation();
                                deleteChat.mutate(chat.id, {
                                    onSuccess: () => {
                                        if (isActiveChat) {
                                            router.push('/app');
                                        }
                                    },
                                });
                            }}
                            className="text-gray-400 hover:text-red-300"
                            aria-label="Delete chat"
                        >
                            <Trash size={14} />
                        </button>
                    </div>
                )}
                {isActiveChat && !isEditing && (
                    <motion.div
                        layoutId="recent-item-pill"
                        className="absolute inset-0 rounded-lg bg-white/5 border border-white/5 shadow-sm"
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                )}
                {!isActiveChat && !isEditing && (
                    <div className="absolute inset-0 rounded-lg bg-white/5 border border-white/5 shadow-sm opacity-0 transition-opacity group-hover:opacity-100" />
                )}
            </div>
        );
    };

    // Mobile View
    if (!isDesktop) {
        return (
            <>
                <button
                    onClick={() => setIsMobileOpen(true)}
                    className="fixed top-4 right-4 z-50 p-2 bg-[#0B0E13] border border-white/10 rounded-full text-white shadow-lg"
                >
                    <Menu size={20} />
                </button>

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
                                <div className="flex items-center justify-between h-[72px] px-5 border-b border-white/5">
                                    <SidebarLogo />
                                    <button onClick={() => setIsMobileOpen(false)} className="text-gray-400 hover:text-white">
                                        <PanelLeftClose size={20} />
                                    </button>
                                </div>

                                <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                                    <div className="px-3 space-y-1 mt-4">
                                        {/* Streak Item - Mobile */}
                                        {streakData && streakData.current_streak > 0 && (
                                            <div className="flex items-center w-full space-x-3 px-3 py-2.5 rounded-full">
                                                <div className="relative shrink-0">
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
                                                        <Flame className="h-5 w-5 text-orange-400" />
                                                    </motion.div>
                                                    <span className="absolute -top-1 -right-1 text-[8px] font-bold text-orange-400">
                                                        {streakData.current_streak}
                                                    </span>
                                                </div>
                                                <span className="font-medium text-sm text-orange-400">
                                                    {streakData.current_streak} day{streakData.current_streak !== 1 ? 's' : ''} streak
                                                </span>
                                            </div>
                                        )}

                                        {navItems.map(item => (
                                            <NavItem
                                                key={item.path}
                                                // @ts-ignore
                                                icon={item.icon}
                                                path={item.path}
                                                label={item.title}
                                                active={isActive(item.path)}
                                                isCollapsed={false}
                                                onModalClick={() => handleNavClick(item.title, item.path)}
                                            />
                                        ))}
                                    </div>
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
                                            {activeTab === 'chats' && (
                                                isLoadingChats ? (
                                                    <div className="flex justify-center py-4"><Loader2 className="h-4 w-4 animate-spin text-gray-600" /></div>
                                                ) : sortedChats.length > 0 ? (
                                                    sortedChats.map((chat: any) => renderChatItem(chat, {
                                                        showIcon: true,
                                                        onSelect: () => setIsMobileOpen(false),
                                                    }))
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

                                    <SidebarUser user={user} profile={profile} isCollapsed={false} />
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
            isCollapsed ? "w-20 group/sidebar" : "w-[280px]"
        )}>
            {/* Header with Integrated Toggle */}
            <div className={cn("flex items-center h-[72px] transition-all", isCollapsed ? "justify-center" : "px-5 justify-between")}>
                {!isCollapsed ? (
                    <>
                        <SidebarLogo />
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
                        className="w-10 h-10 flex items-center justify-center transition-all relative"
                    >
                        <div className="absolute inset-0 flex items-center justify-center transition-all duration-300 opacity-100 group-hover/sidebar:opacity-0 group-hover/sidebar:scale-75">
                            <Image
                                src="/images/image.png"
                                alt="Expand"
                                width={24}
                                height={24}
                            />
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center transition-all duration-300 opacity-0 scale-75 group-hover/sidebar:opacity-100 group-hover/sidebar:scale-100 text-gray-400">
                            <PanelLeft size={20} />
                        </div>
                    </button>
                )}
            </div>

            {/* Main Nav */}
            <div className="px-3 space-y-1">
                {/* Streak Item - Always at top */}
                {streakData && streakData.current_streak > 0 && (
                    <div
                        className={cn(
                            "flex items-center transition-all duration-200 group relative",
                            isCollapsed
                                ? "justify-center w-12 h-12 rounded-full mx-auto"
                                : "w-full space-x-3 px-3 py-2.5 rounded-full"
                        )}
                    >
                        <div className="relative z-10 flex items-center gap-3">
                            <div className="relative shrink-0">
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
                                    <Flame className="h-5 w-5 text-orange-400" />
                                </motion.div>
                                <span className="absolute -top-1 -right-1 text-[8px] font-bold text-orange-400">
                                    {streakData.current_streak}
                                </span>
                            </div>
                            {!isCollapsed && (
                                <span className="font-medium text-sm text-orange-400">
                                    {streakData.current_streak} day{streakData.current_streak !== 1 ? 's' : ''} streak
                                </span>
                            )}
                        </div>
                    </div>
                )}

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
                                                                    {renderChatItem(chat)}
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
                                                        icon={LayoutPanelTop}
                                                        active={isRecentActive('boards', board.id)}
                                                        href={`/app/boards/${board.id}`}
                                                    />
                                                </StaggerItem>
                                            ))
                                        ) : (
                                            <div className="px-3 py-8 text-[10px] text-gray-500 text-center border border-dashed border-white/5 rounded-xl">No boards created</div>
                                        )
                                    )}

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

            <SidebarUser user={user} profile={profile} isCollapsed={isCollapsed} />

            <SidebarRecentsModal
                isOpen={isRecentsModalOpen}
                onOpenChange={setIsRecentsModalOpen}
                tab={recentsModalTab}
                isLoading={isLoadingChats}
                chats={sortedAllChats}
                handleOpenChat={handleOpenChat}
                router={router}
                groupedChats={groupedAllChats}
            />
        </aside>
    );
}
