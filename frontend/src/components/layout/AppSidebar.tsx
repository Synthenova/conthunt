"use client";

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutGrid,
    Home,
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

const navItems = [
    { title: "Home", path: "/app", icon: Home },
    { title: "Boards", path: "/app/boards", icon: LayoutGrid },
    { title: "Chats", path: "/app/chats", icon: MessageSquare },
    // { title: "Searches", path: "/app/searches", icon: Search },
];

export function AppSidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [activeTab, setActiveTab] = useState<'boards' | 'chats' | 'searches'>('chats');
    const [isRecentsModalOpen, setIsRecentsModalOpen] = useState(false);
    const [recentsModalTab, setRecentsModalTab] = useState<'chats' | 'searches'>('chats');

    const { openSidebar, setActiveChatId } = useChatStore();
    const { history, isLoadingHistory } = useSearch();
    const { boards, isLoadingBoards } = useBoards();
    const { data: allChats = [], isLoading: isLoadingChats } = useChatList(undefined, { setStore: false });
    const { user, profile } = useUser();

    const sortedAllChats = useMemo(() => {
        return [...allChats].sort((a, b) => {
            const aTime = new Date(a.updated_at).getTime();
            const bTime = new Date(b.updated_at).getTime();
            return bTime - aTime;
        });
    }, [allChats]);
    const sortedChats = useMemo(() => sortedAllChats.slice(0, 10), [sortedAllChats]);
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

    const NavItem = ({ icon: Icon, label, path }: any) => {
        const active = isActive(path);
        const isModalNav = label === 'Chats' || label === 'Searches';
        const classes = cn(
            "flex items-center transition-all duration-200 group relative",
            isCollapsed
                ? "justify-center w-12 h-12 rounded-xl mx-auto"
                : "w-full space-x-3 px-3 py-2.5 rounded-xl",
            active
                ? "bg-primary/10 text-primary"
                : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
        );
        const iconClasses = cn("transition-colors shrink-0", active ? "text-primary" : "group-hover:text-gray-200");
        return (
            isModalNav ? (
                <button
                    type="button"
                    onClick={() => handleNavClick(label, path)}
                    className={classes}
                >
                    <Icon size={20} className={iconClasses} />
                    {!isCollapsed && (
                        <span className="font-medium text-sm whitespace-nowrap overflow-hidden transition-all duration-300 origin-left">
                            {label}
                        </span>
                    )}
                    {active && (
                        <div className={cn(
                            "absolute bg-primary shadow-[0_0_8px_rgba(59,130,246,0.8)] rounded-full",
                            isCollapsed ? "top-2 right-2 w-1.5 h-1.5" : "right-3 w-1.5 h-1.5"
                        )} />
                    )}
                </button>
            ) : (
                <Link href={path} className={classes}>
                    <Icon size={20} className={iconClasses} />
                    {!isCollapsed && (
                        <span className="font-medium text-sm whitespace-nowrap overflow-hidden transition-all duration-300 origin-left">
                            {label}
                        </span>
                    )}
                    {active && (
                        <div className={cn(
                            "absolute bg-primary shadow-[0_0_8px_rgba(59,130,246,0.8)] rounded-full",
                            isCollapsed ? "top-2 right-2 w-1.5 h-1.5" : "right-3 w-1.5 h-1.5"
                        )} />
                    )}
                </Link>
            )
        );
    };

    const roleLabels: Record<string, string> = {
        free: "Free Plan",
        creator: "Creator Plan",
        pro_research: "Pro Research"
    };

    return (
        <aside className={cn(
            "relative z-50 h-full bg-[#07090C] border-r border-white/5 flex flex-col transition-all duration-300 ease-in-out",
            isCollapsed ? "w-20" : "w-[260px]"
        )}>
            {/* Toggle Button */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute -right-3 top-8 w-6 h-6 bg-[#0D1118] border border-white/10 rounded-full items-center justify-center text-gray-400 hover:text-white hover:scale-110 transition-all z-50 shadow-lg"
            >
                {isCollapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
            </button>

            {/* Header */}
            <div className={cn("flex items-center h-[72px]", isCollapsed ? "justify-center px-0" : "px-5 justify-between")}>
                <div className="flex items-center space-x-3 text-white">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
                        <span className="font-bold text-lg">C</span>
                    </div>
                    {!isCollapsed && (
                        <span className="font-semibold text-lg tracking-tight whitespace-nowrap overflow-hidden animate-in fade-in duration-300">
                            Conthunt
                        </span>
                    )}
                </div>
            </div>

            {/* Main Nav */}
            <div className="px-3 space-y-1">
                {navItems.map(item => (
                    <NavItem key={item.path} {...item} label={item.title} />
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
                        <div className="flex p-1 bg-white/5 rounded-lg mb-4">
                            {(['boards', 'chats'] as const).map((tab) => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={cn(
                                        "flex-1 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-md transition-all",
                                        activeTab === tab
                                            ? "bg-white/10 text-white shadow-sm"
                                            : "text-gray-500 hover:text-gray-300"
                                    )}
                                >
                                    {tab}
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
                                            sortedChats.map((chat: any) => (
                                                <StaggerItem key={chat.id}>
                                                    <button
                                                        onClick={() => handleOpenChat(chat.id)}
                                                        className={cn(
                                                            "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-left group",
                                                            isRecentActive('chats', chat.id)
                                                                ? "bg-white/10 text-white"
                                                                : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                                                        )}
                                                    >
                                                        <MessageSquare size={14} className="shrink-0 opacity-50 group-hover:opacity-100" />
                                                        <span className="text-xs truncate font-medium">{chat.title || "New Chat"}</span>
                                                    </button>
                                                </StaggerItem>
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
                                                    <Link
                                                        href={`/app/boards/${board.id}`}
                                                        className={cn(
                                                            "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all group",
                                                            isRecentActive('boards', board.id)
                                                                ? "bg-white/10 text-white"
                                                                : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                                                        )}
                                                    >
                                                        <LayoutGrid size={14} className="shrink-0 opacity-50 group-hover:opacity-100" />
                                                        <span className="text-xs truncate font-medium">{board.name}</span>
                                                    </Link>
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
                    <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-xs text-blue-400 font-bold shrink-0">
                        {user?.email?.[0].toUpperCase() || "U"}
                    </div>
                    {!isCollapsed && (
                        <>
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-semibold text-gray-200 truncate">
                                    {user?.displayName || user?.email?.split('@')[0] || "User"}
                                </p>
                                <p className="text-[9px] font-bold text-blue-400 uppercase tracking-tighter">
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
                <DialogContent className="bg-[#0B0E13] border border-white/10 text-white max-w-md">
                    <DialogHeader>
                        <DialogTitle className="text-base">
                            {recentsModalTab === 'chats' ? 'All Chats' : 'All Searches'}
                        </DialogTitle>
                    </DialogHeader>
                    <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1 custom-scrollbar">
                        {recentsModalTab === 'chats' ? (
                            isLoadingChats ? (
                                <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-gray-500" /></div>
                            ) : sortedAllChats.length > 0 ? (
                                sortedAllChats.map((chat: any) => (
                                    <button
                                        key={chat.id}
                                        onClick={() => {
                                            handleOpenChat(chat.id);
                                            setIsRecentsModalOpen(false);
                                        }}
                                        className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/5 transition-all text-left"
                                    >
                                        <MessageSquare size={14} className="shrink-0 opacity-60" />
                                        <span className="text-sm truncate font-medium">{chat.title || "New Chat"}</span>
                                    </button>
                                ))
                            ) : (
                                <div className="px-3 py-8 text-xs text-gray-500 text-center border border-dashed border-white/10 rounded-xl">
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
