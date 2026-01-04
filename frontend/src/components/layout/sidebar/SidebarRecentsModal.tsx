"use client";

import React, { useEffect, useRef, useState } from 'react';
import { Search, Loader2, MessageSquare, Pencil } from 'lucide-react';
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useRenameChat } from "@/hooks/useChat";

interface SidebarRecentsModalProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    tab: 'chats' | 'searches';
    isLoading: boolean;
    chats: any[]; // Using generalized type for now, ideally strictly typed
    handleOpenChat: (chat: any) => void;
    router: any; // NextRouter
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
    const editInputRef = useRef<HTMLInputElement | null>(null);
    const renameChat = useRenameChat();

    useEffect(() => {
        if (editingChatId) {
            editInputRef.current?.focus();
            editInputRef.current?.select();
        }
    }, [editingChatId]);

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

    return (
        <Dialog open={isOpen} onOpenChange={onOpenChange}>
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
                            onOpenChange(false);
                            router.push('/app');
                        }}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-white hover:bg-white/5 transition-all text-left font-medium text-sm group"
                    >
                        <MessageSquare size={16} className="shrink-0 text-white" />
                        New chat
                    </button>
                </div>

                <div className="max-h-[60vh] overflow-y-auto px-2 pb-4 custom-scrollbar">
                    {tab === 'chats' ? (
                        isLoading ? (
                            <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-gray-500" /></div>
                        ) : chats.length > 0 ? (
                            Object.entries(groupedChats).map(([group, groupChats]) => (
                                groupChats.length > 0 && (
                                    <div key={group} className="mt-4 first:mt-2">
                                        <div className="px-3 mb-2 text-[11px] font-medium text-gray-500">{group}</div>
                                        <div className="space-y-0.5">
                                            {groupChats.map((chat: any) => (
                                                <div
                                                    key={chat.id}
                                                    role="button"
                                                    tabIndex={0}
                                                    onClick={() => {
                                                        if (editingChatId === chat.id) return;
                                                        handleOpenChat(chat);
                                                        onOpenChange(false);
                                                    }}
                                                    onKeyDown={(event) => {
                                                        if (editingChatId === chat.id) return;
                                                        if (event.key === 'Enter' || event.key === ' ') {
                                                            event.preventDefault();
                                                            handleOpenChat(chat);
                                                            onOpenChange(false);
                                                        }
                                                    }}
                                                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all text-left group relative"
                                                >
                                                    <MessageSquare size={16} className="shrink-0 opacity-70 group-hover:opacity-100 transition-opacity" />
                                                    {editingChatId === chat.id ? (
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
                                                            className="w-full bg-transparent text-sm text-white placeholder:text-gray-500 outline-none"
                                                        />
                                                    ) : (
                                                        <span className="text-sm truncate">{chat.title || "New Chat"}</span>
                                                    )}
                                                    {editingChatId !== chat.id && (
                                                        <button
                                                            type="button"
                                                            onClick={(event) => {
                                                                event.stopPropagation();
                                                                startChatEdit(chat.id, chat.title);
                                                            }}
                                                            className="ml-auto text-gray-400 hover:text-gray-200 opacity-0 group-hover:opacity-100 transition-opacity"
                                                            aria-label="Rename chat"
                                                        >
                                                            <Pencil size={14} />
                                                        </button>
                                                    )}
                                                </div>
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
                </div>
            </DialogContent>
        </Dialog>
    );
};
