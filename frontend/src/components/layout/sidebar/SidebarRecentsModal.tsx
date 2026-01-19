"use client";

import React, { useEffect, useRef, useState } from 'react';
import { Search, Loader2, MessageSquare, Pencil, Trash, CornerDownLeft, Check, X } from 'lucide-react';
import { Dialog, DialogContent, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { useRenameChat, useDeleteChat } from "@/hooks/useChat";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

interface SidebarRecentsModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    tab: 'chats' | 'searches';
    isLoading: boolean;
    chats: any[];
    handleOpenChat: (chat: any) => void;
    router: any;
    groupedChats: Record<string, any[]>;
}

export const SidebarRecentsModal = ({
    isOpen,
    onOpenChange,
    tab,
    isLoading,
    chats,
    handleOpenChat,
    router,
    groupedChats
}: SidebarRecentsModalProps) => {
    const [editingChatId, setEditingChatId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [hoveredChatId, setHoveredChatId] = useState<string | null>(null);
    const editInputRef = useRef<HTMLInputElement | null>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);
    const itemRefs = useRef<(HTMLDivElement | null)[]>([]);
    const renameChat = useRenameChat();
    const deleteChat = useDeleteChat();

    // Flatten chats for keyboard navigation
    const flatChats = React.useMemo(() => {
        return Object.values(groupedChats).flat();
    }, [groupedChats]);

    useEffect(() => {
        if (isOpen) {
            setSelectedIndex(0);
            // Reset refs array when chats change or modal opens
            itemRefs.current = itemRefs.current.slice(0, flatChats.length);
        }
    }, [isOpen, flatChats.length]);

    useEffect(() => {
        if (editingChatId) {
            editInputRef.current?.focus();
            editInputRef.current?.select();
        }
    }, [editingChatId]);

    // Track previous length to detect deletions
    const prevFlatChatsLengthRef = useRef(flatChats.length);

    useEffect(() => {
        // If length decreased (deletion) and mouse isn't hovering
        if (flatChats.length < prevFlatChatsLengthRef.current && hoveredChatId === null) {
            setSelectedIndex(prev => Math.max(0, prev - 1));
        }
        prevFlatChatsLengthRef.current = flatChats.length;
    }, [flatChats.length, hoveredChatId]);

    // Auto-scroll effect
    useEffect(() => {
        if (isOpen && itemRefs.current[selectedIndex]) {
            itemRefs.current[selectedIndex]?.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
            });
        }
    }, [selectedIndex, isOpen]);

    // Keyboard navigation
    useEffect(() => {
        if (!isOpen) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            if (editingChatId) return;

            // Allow typing in search box without triggering shortcuts
            if (document.activeElement === searchInputRef.current) {
                if (['ArrowDown', 'ArrowUp', 'Enter'].includes(e.key)) {
                    // Allow navigation keys to work even from input
                } else {
                    return;
                }
            }

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    setSelectedIndex(prev => Math.min(prev + 1, flatChats.length - 1));
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    setSelectedIndex(prev => Math.max(prev - 1, 0));
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (flatChats[selectedIndex]) {
                        handleOpenChat(flatChats[selectedIndex]);
                        onOpenChange(false);
                    }
                    break;
                case 'e':
                case 'r':
                case 'E':
                case 'R':
                    e.preventDefault();
                    const chatToEdit = flatChats[selectedIndex];
                    if (chatToEdit) {
                        startChatEdit(chatToEdit.id, chatToEdit.title);
                    }
                    break;
                case 'd':
                case 'D':
                    e.preventDefault();
                    const chatToDelete = flatChats[selectedIndex];
                    if (chatToDelete) {
                        deleteChat.mutate(chatToDelete.id);
                    }
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, flatChats, selectedIndex, editingChatId, handleOpenChat, deleteChat, onOpenChange]);


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

    const formatTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        const diffInMinutes = Math.floor(diffInSeconds / 60);
        if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) return `${diffInHours}h ago`;
        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays < 7) return `${diffInDays}d ago`;
        return date.toLocaleDateString();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
            <DialogContent
                showCloseButton={false}
                onOpenAutoFocus={(e) => e.preventDefault()}
                className="bg-[#0f0f0f] border border-white/10 text-gray-200 p-0 gap-0 overflow-hidden shadow-2xl rounded-3xl max-w-3xl sm:max-w-3xl w-full outline-none transition-all duration-200"
            >
                <VisuallyHidden>
                    <DialogTitle>Search</DialogTitle>
                </VisuallyHidden>

                {/* Search Header - Spacious */}
                <div className="p-6 pb-4 flex items-center gap-4">
                    <Search size={22} className="text-gray-500" />
                    <input
                        ref={searchInputRef}
                        className="bg-transparent border-none outline-none text-xl placeholder:text-gray-600 flex-1 text-white font-medium h-full placeholder:font-normal"
                        placeholder="Search..."
                    />
                    {isLoading && <Loader2 className="h-5 w-5 animate-spin text-gray-600" />}
                    <DialogClose asChild>
                        <button className="text-gray-500 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-full outline-none">
                            <X size={20} />
                        </button>
                    </DialogClose>
                </div>

                <div className="px-2 pb-2">
                    <div className="h-[1px] bg-white/5 mx-4" />
                </div>

                {/* Content Area */}
                <div className="max-h-[55vh] overflow-y-auto px-4 pb-4 custom-scrollbar">
                    {/* Actions Section */}
                    <div className="py-4">
                        <div className="px-4 py-2 text-xs font-bold text-gray-600 uppercase tracking-widest mb-1">Actions</div>
                        <button
                            onClick={() => {
                                onOpenChange(false);
                                router.push('/app');
                            }}
                            className="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl text-white hover:bg-white/5 transition-all text-left font-medium group"
                        >
                            <MessageSquare size={18} className="text-[rgb(99,112,136)] group-hover:text-white transition-colors" />
                            <span className="text-[rgb(99,112,136)] group-hover:text-white transition-colors relative -top-[1px]">Create new chat</span>
                        </button>
                    </div>

                    {/* Chats List */}
                    <div className="py-2 space-y-6">
                        {tab === 'chats' && groupedChats && Object.entries(groupedChats).map(([group, groupChats]) => (
                            groupChats.length > 0 && (
                                <div key={group}>
                                    <div className="px-4 py-2 text-xs font-bold text-gray-600 uppercase tracking-widest mb-2">{group}</div>
                                    <div className="space-y-1">
                                        {groupChats.map((chat: any) => {
                                            const isSelected = flatChats[selectedIndex]?.id === chat.id;
                                            const isEditing = editingChatId === chat.id;
                                            const isHovered = hoveredChatId === chat.id;

                                            // Find index in flat list to assign ref
                                            const flatIndex = flatChats.findIndex(c => c.id === chat.id);

                                            return (
                                                <div
                                                    key={chat.id}
                                                    ref={el => { itemRefs.current[flatIndex] = el; }}
                                                    role="button"
                                                    tabIndex={0}
                                                    onClick={() => {
                                                        if (isEditing) return;
                                                        handleOpenChat(chat);
                                                        onOpenChange(false);
                                                    }}
                                                    onMouseEnter={() => {
                                                        setHoveredChatId(chat.id);
                                                        const idx = flatChats.findIndex(c => c.id === chat.id);
                                                        if (idx !== -1) setSelectedIndex(idx);
                                                    }}
                                                    onMouseLeave={() => setHoveredChatId(null)}
                                                    className={cn(
                                                        "w-full flex items-center justify-between px-4 py-3.5 rounded-2xl transition-all text-left group cursor-pointer border border-transparent min-h-[56px]",
                                                        isSelected ? "bg-white/10" : "hover:bg-white/5",
                                                        isEditing && "border-white/20 bg-black/50"
                                                    )}
                                                >
                                                    <div className="flex-1 min-w-0 flex items-center gap-3 mr-4">
                                                        {isEditing ? (
                                                            <div className="flex items-center gap-2 w-full">
                                                                <input
                                                                    ref={editInputRef}
                                                                    value={editingTitle}
                                                                    onChange={(event) => setEditingTitle(event.target.value)}
                                                                    onKeyDown={(event) => {
                                                                        if (event.key === 'Enter') {
                                                                            event.preventDefault();
                                                                            event.stopPropagation();
                                                                            commitChatEdit();
                                                                        }
                                                                        if (event.key === 'Escape') {
                                                                            event.preventDefault();
                                                                            event.stopPropagation();
                                                                            cancelChatEdit();
                                                                        }
                                                                        // Stop propagation for all keys to prevent navigation while editing
                                                                        event.stopPropagation();
                                                                    }}
                                                                    onClick={(e) => e.stopPropagation()}
                                                                    className="flex-1 bg-transparent text-base text-white placeholder:text-gray-500 outline-none font-medium p-0"
                                                                />
                                                            </div>
                                                        ) : (
                                                            <span className={cn(
                                                                "text-base font-medium truncate transition-colors",
                                                                isSelected ? "text-white" : "text-[rgb(99,112,136)] group-hover:text-white"
                                                            )}>
                                                                {(chat.title || "New Chat").length > 100
                                                                    ? (chat.title || "New Chat").substring(0, 100) + "..."
                                                                    : (chat.title || "New Chat")}
                                                            </span>
                                                        )}
                                                    </div>

                                                    {/* Right Side: Date or Actions - Keeping it minimal as per user request */}
                                                    <div className="flex items-center gap-2">
                                                        {isEditing ? (
                                                            <>
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        commitChatEdit();
                                                                    }}
                                                                    className="p-1 hover:bg-white/10 rounded-full text-green-400 hover:text-green-300 transition-colors"
                                                                >
                                                                    <Check size={16} />
                                                                </button>
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        cancelChatEdit();
                                                                    }}
                                                                    className="p-1 hover:bg-white/10 rounded-full text-red-400 hover:text-red-300 transition-colors"
                                                                >
                                                                    <X size={16} />
                                                                </button>
                                                            </>
                                                        ) : (
                                                            <>
                                                                {(isHovered || isSelected) ? (
                                                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                        <button
                                                                            onClick={(e) => {
                                                                                e.stopPropagation();
                                                                                startChatEdit(chat.id, chat.title);
                                                                            }}
                                                                            className="p-1.5 text-gray-500 hover:text-white hover:bg-white/10 rounded-md transition-all"
                                                                            title="Edit"
                                                                        >
                                                                            <Pencil size={14} />
                                                                        </button>
                                                                        <button
                                                                            onClick={(e) => {
                                                                                e.stopPropagation();
                                                                                deleteChat.mutate(chat.id);
                                                                            }}
                                                                            className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-all"
                                                                            title="Delete"
                                                                        >
                                                                            <Trash size={14} />
                                                                        </button>
                                                                    </div>
                                                                ) : null}

                                                                <span className={cn(
                                                                    "text-xs text-gray-500 whitespace-nowrap transition-colors",
                                                                    (isHovered || isSelected) ? "opacity-0 hidden" : "opacity-100 block"
                                                                )}>
                                                                    {chat.updated_at ? formatTimeAgo(chat.updated_at) : ''}
                                                                </span>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )
                        ))}
                    </div>
                </div>

                {/* Footer with Shortcuts */}
                <div className="px-6 py-4 border-t border-white/5 bg-white/[0.02] flex items-center justify-end text-xs text-gray-500 select-none">
                    <div className="flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <span>Go</span>
                            <div className="h-5 min-w-[20px] px-1.5 flex items-center justify-center rounded bg-white/10 text-gray-300 font-sans border border-white/5 shadow-sm">
                                <CornerDownLeft size={10} />
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <span>Edit</span>
                            <div className="h-5 px-1.5 flex items-center justify-center rounded bg-white/10 text-gray-300 font-sans border border-white/5 shadow-sm">
                                <span className="text-[10px]">E</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <span>Rename</span>
                            <div className="h-5 px-1.5 flex items-center justify-center rounded bg-white/10 text-gray-300 font-sans border border-white/5 shadow-sm">
                                <span className="text-[10px]">R</span>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <span>Delete</span>
                            <div className="h-5 px-1.5 flex items-center justify-center rounded bg-white/10 text-gray-300 font-sans border border-white/5 shadow-sm">
                                <span className="text-[10px]">D</span>
                            </div>
                        </div>
                    </div>
                </div>

            </DialogContent>
        </Dialog>
    );
};
