
import { useState, useRef, useEffect } from "react";
import { useRenameChat, useDeleteChat } from "@/hooks/useChat";
import { useRouter } from "next/navigation";

export function useChatTitle(chatId: string, activeChatTitle: string) {
    const router = useRouter();
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [editingTitle, setEditingTitle] = useState('');
    const editTitleRef = useRef<HTMLInputElement | null>(null);
    const renameChat = useRenameChat();
    const deleteChat = useDeleteChat();

    useEffect(() => {
        if (isEditingTitle) {
            editTitleRef.current?.focus();
            editTitleRef.current?.select();
        }
    }, [isEditingTitle]);

    const startTitleEdit = () => {
        setIsEditingTitle(true);
        setEditingTitle(activeChatTitle);
    };

    const cancelTitleEdit = () => {
        setIsEditingTitle(false);
        setEditingTitle('');
    };

    const commitTitleEdit = async () => {
        const nextTitle = editingTitle.trim();
        cancelTitleEdit();
        if (!nextTitle) return;
        try {
            await renameChat.mutateAsync({ chatId, title: nextTitle });
        } catch (err) {
            console.error(err);
        }
    };

    const onDeleteChat = () => {
        deleteChat.mutate(chatId, {
            onSuccess: () => router.push("/app"),
        });
    };

    return {
        isEditingTitle,
        editingTitle,
        setEditingTitle,
        editTitleRef,
        startTitleEdit,
        cancelTitleEdit,
        commitTitleEdit,
        onDeleteChat
    };
}
