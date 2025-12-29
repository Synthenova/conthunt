"use client";

import { useMemo, useState } from "react";
import {
    ChevronDown,
    ChevronRight,
    History,
    LayoutDashboard,
    Loader2,
    MessageSquare,
    Search,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuAction,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuSub,
    SidebarMenuSubButton,
    SidebarMenuSubItem,
    SidebarRail,
    SidebarTrigger,
} from "@/components/ui/sidebar";
import { LogoutButton } from "@/components/logout-button";
import { useSearch } from "@/hooks/useSearch";
import { useBoards } from "@/hooks/useBoards";
import { useChatList } from "@/hooks/useChat";
import { useChatStore } from "@/lib/chatStore";

const navItems = [
    {
        title: "Search",
        url: "/app",
        icon: Search,
    },
    {
        title: "History",
        url: "/app/history",
        icon: History,
    },
    {
        title: "Boards",
        url: "/app/boards",
        icon: LayoutDashboard,
    },
];

const TITLE_LIMIT = 28;

function truncateText(value: string, limit: number) {
    if (value.length <= limit) return value;
    return value.slice(0, limit - 1).trimEnd() + "...";
}

export function AppSidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const { openSidebar, setActiveChatId } = useChatStore();
    const { history, isLoadingHistory } = useSearch();
    const { boards, isLoadingBoards } = useBoards();
    const { data: allChats = [], isLoading: isLoadingChats } = useChatList(undefined, { setStore: false });

    const [expandedSearches, setExpandedSearches] = useState<Set<string>>(new Set());
    const [expandedBoards, setExpandedBoards] = useState<Set<string>>(new Set());
    const [isSearchExpanded, setIsSearchExpanded] = useState(false);
    const [isBoardsExpanded, setIsBoardsExpanded] = useState(false);
    const [isChatsExpanded, setIsChatsExpanded] = useState(false);

    const sortedChats = useMemo(() => {
        return [...allChats].sort((a, b) => {
            const aTime = new Date(a.updated_at).getTime();
            const bTime = new Date(b.updated_at).getTime();
            return bTime - aTime;
        });
    }, [allChats]);

    const chatsBySearchId = useMemo(() => {
        const map: Record<string, typeof allChats> = {};
        sortedChats.forEach((chat) => {
            if (chat.context_type !== "search" || !chat.context_id) return;
            const key = chat.context_id;
            if (!map[key]) map[key] = [];
            map[key].push(chat);
        });
        return map;
    }, [sortedChats, allChats]);

    const chatsByBoardId = useMemo(() => {
        const map: Record<string, typeof allChats> = {};
        sortedChats.forEach((chat) => {
            if (chat.context_type !== "board" || !chat.context_id) return;
            const key = chat.context_id;
            if (!map[key]) map[key] = [];
            map[key].push(chat);
        });
        return map;
    }, [sortedChats, allChats]);

    const toggleSet = (value: string, setter: (updater: (prev: Set<string>) => Set<string>) => void) => {
        setter((prev) => {
            const next = new Set(prev);
            if (next.has(value)) {
                next.delete(value);
            } else {
                next.add(value);
            }
            return next;
        });
    };

    const handleOpenChat = (chat: (typeof allChats)[number]) => {
        setActiveChatId(chat.id);
        openSidebar();
        if (chat.context_type === "board" && chat.context_id) {
            router.push(`/app/boards/${chat.context_id}`);
        } else if (chat.context_type === "search" && chat.context_id) {
            router.push(`/app/searches/${chat.context_id}`);
        }
    };

    return (
        <Sidebar
            collapsible="icon"
            className="border-r border-white/5"
        >
            <SidebarHeader className="p-4 group-data-[collapsible=icon]:p-2 transition-all">
                <div className="flex items-center justify-between px-2 group-data-[collapsible=icon]:px-0">
                    <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shrink-0">
                            <span className="font-bold text-lg">C</span>
                        </div>
                        <span className="font-semibold text-lg group-data-[collapsible=icon]:hidden">Conthunt</span>
                    </div>
                    <SidebarTrigger className="group-data-[collapsible=icon]:hidden ml-auto h-8 w-8" />
                </div>
                <div className="hidden group-data-[collapsible=icon]:flex items-center justify-center py-2">
                    <SidebarTrigger className="h-8 w-8" />
                </div>
            </SidebarHeader>
            <SidebarContent className="gap-1">
                <SidebarGroup>
                    <SidebarGroupLabel className="group-data-[collapsible=icon]:hidden">Navigation</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {navItems.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton
                                        asChild
                                        isActive={pathname === item.url || pathname?.startsWith(`${item.url}/`)}
                                        tooltip={item.title}
                                    >
                                        <Link href={item.url}>
                                            <item.icon className="h-4 w-4" />
                                            <span>{item.title}</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>

                <SidebarGroup className={isSearchExpanded ? "py-2" : "py-1"}>
                    <SidebarGroupLabel asChild className="group-data-[collapsible=icon]:hidden">
                        <button
                            type="button"
                            onClick={() => setIsSearchExpanded((prev) => !prev)}
                            className="flex w-full items-center justify-between"
                        >
                            <span>Search History</span>
                            {isSearchExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </button>
                    </SidebarGroupLabel>
                    {isSearchExpanded && (
                        <SidebarGroupContent>
                            <SidebarMenu>
                                {isLoadingHistory ? (
                                    <SidebarMenuItem>
                                        <div className="flex items-center justify-center py-2 text-muted-foreground">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        </div>
                                    </SidebarMenuItem>
                                ) : history.length === 0 ? (
                                    <SidebarMenuItem>
                                        <div className="px-3 py-2 text-xs text-muted-foreground">
                                            No searches yet
                                        </div>
                                    </SidebarMenuItem>
                                ) : (
                                    history.map((item) => {
                                        const searchId = String(item.id);
                                        const chatsForSearch = chatsBySearchId[searchId] || [];
                                        const isExpanded = expandedSearches.has(searchId);
                                        const hasChats = chatsForSearch.length > 0;

                                        return (
                                            <SidebarMenuItem key={item.id}>
                                                <SidebarMenuButton
                                                    asChild
                                                    isActive={pathname === `/app/searches/${searchId}`}
                                                    tooltip={item.query}
                                                >
                                                    <Link href={`/app/searches/${searchId}`} onClick={() => openSidebar()}>
                                                        <span className="flex-1 min-w-0 truncate">
                                                            {truncateText(item.query, TITLE_LIMIT)}
                                                        </span>
                                                    </Link>
                                                </SidebarMenuButton>
                                                <SidebarMenuAction
                                                    disabled={!hasChats}
                                                    onClick={(event) => {
                                                        event.preventDefault();
                                                        event.stopPropagation();
                                                        if (!hasChats) return;
                                                        toggleSet(searchId, setExpandedSearches);
                                                    }}
                                                >
                                                    {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                                </SidebarMenuAction>
                                                {isExpanded && hasChats && (
                                                    <SidebarMenuSub>
                                                        {chatsForSearch.map((chat) => (
                                                            <SidebarMenuSubItem key={chat.id}>
                                                                <SidebarMenuSubButton
                                                                    asChild
                                                                    isActive={false}
                                                                >
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => handleOpenChat(chat)}
                                                                        className="w-full text-left"
                                                                    >
                                                                        <MessageSquare className="h-3.5 w-3.5" />
                                                                        <span className="truncate">
                                                                            {truncateText(chat.title || "New Chat", TITLE_LIMIT)}
                                                                        </span>
                                                                    </button>
                                                                </SidebarMenuSubButton>
                                                            </SidebarMenuSubItem>
                                                        ))}
                                                    </SidebarMenuSub>
                                                )}
                                            </SidebarMenuItem>
                                        );
                                    })
                                )}
                            </SidebarMenu>
                        </SidebarGroupContent>
                    )}
                </SidebarGroup>

                <SidebarGroup className={isBoardsExpanded ? "py-2" : "py-1"}>
                    <SidebarGroupLabel asChild className="group-data-[collapsible=icon]:hidden">
                        <button
                            type="button"
                            onClick={() => setIsBoardsExpanded((prev) => !prev)}
                            className="flex w-full items-center justify-between"
                        >
                            <span>Boards</span>
                            {isBoardsExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </button>
                    </SidebarGroupLabel>
                    {isBoardsExpanded && (
                        <SidebarGroupContent>
                            <SidebarMenu>
                                {isLoadingBoards ? (
                                    <SidebarMenuItem>
                                        <div className="flex items-center justify-center py-2 text-muted-foreground">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        </div>
                                    </SidebarMenuItem>
                                ) : boards.length === 0 ? (
                                    <SidebarMenuItem>
                                        <div className="px-3 py-2 text-xs text-muted-foreground">
                                            No boards yet
                                        </div>
                                    </SidebarMenuItem>
                                ) : (
                                    boards.map((board) => {
                                        const boardId = String(board.id);
                                        const chatsForBoard = chatsByBoardId[boardId] || [];
                                        const isExpanded = expandedBoards.has(boardId);
                                        const hasChats = chatsForBoard.length > 0;

                                        return (
                                            <SidebarMenuItem key={board.id}>
                                                <SidebarMenuButton
                                                    asChild
                                                    isActive={pathname === `/app/boards/${boardId}`}
                                                    tooltip={board.name}
                                                >
                                                    <Link href={`/app/boards/${boardId}`} onClick={() => openSidebar()}>
                                                        <LayoutDashboard className="h-4 w-4" />
                                                        <span className="flex-1 min-w-0 truncate">
                                                            {truncateText(board.name, TITLE_LIMIT)}
                                                        </span>
                                                    </Link>
                                                </SidebarMenuButton>
                                                <SidebarMenuAction
                                                    disabled={!hasChats}
                                                    onClick={(event) => {
                                                        event.preventDefault();
                                                        event.stopPropagation();
                                                        if (!hasChats) return;
                                                        toggleSet(boardId, setExpandedBoards);
                                                    }}
                                                >
                                                    {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                                </SidebarMenuAction>
                                                {isExpanded && hasChats && (
                                                    <SidebarMenuSub>
                                                        {chatsForBoard.map((chat) => (
                                                            <SidebarMenuSubItem key={chat.id}>
                                                                <SidebarMenuSubButton asChild isActive={false}>
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => handleOpenChat(chat)}
                                                                        className="w-full text-left"
                                                                    >
                                                                        <MessageSquare className="h-3.5 w-3.5" />
                                                                        <span className="truncate">
                                                                            {truncateText(chat.title || "New Chat", TITLE_LIMIT)}
                                                                        </span>
                                                                    </button>
                                                                </SidebarMenuSubButton>
                                                            </SidebarMenuSubItem>
                                                        ))}
                                                    </SidebarMenuSub>
                                                )}
                                            </SidebarMenuItem>
                                        );
                                    })
                                )}
                            </SidebarMenu>
                        </SidebarGroupContent>
                    )}
                </SidebarGroup>

                <SidebarGroup className={isChatsExpanded ? "py-2" : "py-1"}>
                    <SidebarGroupLabel asChild className="group-data-[collapsible=icon]:hidden">
                        <button
                            type="button"
                            onClick={() => setIsChatsExpanded((prev) => !prev)}
                            className="flex w-full items-center justify-between"
                        >
                            <span>Chats</span>
                            {isChatsExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        </button>
                    </SidebarGroupLabel>
                    {isChatsExpanded && (
                        <SidebarGroupContent>
                            <SidebarMenu>
                                {isLoadingChats ? (
                                    <SidebarMenuItem>
                                        <div className="flex items-center justify-center py-2 text-muted-foreground">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        </div>
                                    </SidebarMenuItem>
                                ) : sortedChats.length === 0 ? (
                                    <SidebarMenuItem>
                                        <div className="px-3 py-2 text-xs text-muted-foreground">
                                            No chats yet
                                        </div>
                                    </SidebarMenuItem>
                                ) : (
                                    sortedChats.map((chat) => (
                                        <SidebarMenuItem key={chat.id}>
                                            <SidebarMenuButton
                                                onClick={() => handleOpenChat(chat)}
                                                tooltip={chat.title || "New Chat"}
                                            >
                                                <MessageSquare className="h-4 w-4" />
                                                <span className="flex-1 min-w-0 truncate">
                                                    {truncateText(chat.title || "New Chat", TITLE_LIMIT)}
                                                </span>
                                            </SidebarMenuButton>
                                        </SidebarMenuItem>
                                    ))
                                )}
                            </SidebarMenu>
                        </SidebarGroupContent>
                    )}
                </SidebarGroup>
            </SidebarContent>
            <SidebarFooter>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <LogoutButton className="w-full flex justify-start items-center gap-2 p-2 px-3 text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground rounded-md transition-colors" />
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarFooter>
            <SidebarRail />
        </Sidebar>
    );
}
