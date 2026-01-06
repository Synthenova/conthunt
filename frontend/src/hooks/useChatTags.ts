"use client";

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { BACKEND_URL, authFetch } from '@/lib/api';

async function fetchWithAuth<T>(url: string, options: RequestInit = {}): Promise<T> {
    const res = await authFetch(url, options);
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API request failed');
    }
    return res.json();
}

export type ChatTag = {
    type: 'board' | 'search' | 'media';
    id: string;
    label?: string | null;
    sort_order?: number | null;
    created_at?: string | null;
    source?: 'user' | 'agent';
};

export function useChatTags(chatId: string | null) {
    const queryClient = useQueryClient();

    const tagsQuery = useQuery({
        queryKey: ['chat-tags', chatId],
        queryFn: async () => {
            if (!chatId) return [] as ChatTag[];
            return fetchWithAuth<ChatTag[]>(`${BACKEND_URL}/v1/chats/${chatId}/tags`);
        },
        enabled: !!chatId,
        staleTime: 10000,
    });

    const reorder = useMutation({
        mutationFn: async (orders: Array<{ id: string; sort_order: number }>) => {
            if (!chatId) throw new Error('No chat id');
            return fetchWithAuth(`${BACKEND_URL}/v1/chats/${chatId}/tags/order`, {
                method: 'PATCH',
                body: JSON.stringify({
                    orders: orders.map((o) => ({ tag_id: o.id, sort_order: o.sort_order })),
                }),
            });
        },
        onMutate: async (newOrder) => {
            await queryClient.cancelQueries({ queryKey: ['chat-tags', chatId] });
            const prev = queryClient.getQueryData<ChatTag[]>(['chat-tags', chatId]) || [];
            const orderMap = new Map(newOrder.map((o) => [o.id, o.sort_order]));
            const optimistic = prev
                .slice()
                .sort((a, b) => {
                    const ao = orderMap.has(a.id) ? orderMap.get(a.id)! : a.sort_order ?? 0;
                    const bo = orderMap.has(b.id) ? orderMap.get(b.id)! : b.sort_order ?? 0;
                    return ao - bo;
                })
                .map((t) => (orderMap.has(t.id) ? { ...t, sort_order: orderMap.get(t.id)! } : t));
            queryClient.setQueryData(['chat-tags', chatId], optimistic);
            return { prev };
        },
        onError: (_err, _vars, ctx) => {
            if (ctx?.prev) {
                queryClient.setQueryData(['chat-tags', chatId], ctx.prev);
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ['chat-tags', chatId] });
        },
    });

    const deleteTag = useMutation({
        mutationFn: async (tagId: string) => {
            if (!chatId) throw new Error('No chat id');
            return fetchWithAuth(`${BACKEND_URL}/v1/chats/${chatId}/tags/${tagId}`, {
                method: 'DELETE',
            });
        },
        onMutate: async (tagId) => {
            await queryClient.cancelQueries({ queryKey: ['chat-tags', chatId] });
            const prev = queryClient.getQueryData<ChatTag[]>(['chat-tags', chatId]) || [];
            const optimistic = prev.filter((t) => t.id !== tagId);
            queryClient.setQueryData(['chat-tags', chatId], optimistic);
            return { prev };
        },
        onError: (_err, _vars, ctx) => {
            if (ctx?.prev) {
                queryClient.setQueryData(['chat-tags', chatId], ctx.prev);
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ['chat-tags', chatId] });
        },
    });

    return { tagsQuery, reorder, deleteTag };
}
