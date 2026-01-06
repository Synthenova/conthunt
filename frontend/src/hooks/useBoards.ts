import { useMutation, useQuery, useQueryClient, UseQueryOptions } from "@tanstack/react-query";
import { Board, BoardItem, BoardInsights, CreateBoardRequest } from "@/lib/types/boards";

import { BACKEND_URL, authFetch } from '@/lib/api';

const API_BASE = `${BACKEND_URL}/v1`;

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const res = await authFetch(url, options);
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || "API request failed");
    }

    // Handle 204 No Content
    if (res.status === 204) return null;
    return res.json();
}

/**
 * Hook for all board-related operations.
 */
export function useBoards({ checkItemId }: { checkItemId?: string } = {}) {
    const queryClient = useQueryClient();

    // GET /v1/boards - List all boards
    const boardsQuery = useQuery<Board[]>({
        queryKey: ["boards", checkItemId],
        queryFn: () => fetchWithAuth(`${API_BASE}/boards${checkItemId ? `?check_item_id=${checkItemId}` : ''}`),
    });

    // GET /v1/boards/:id - Get single board
    const getBoard = (id: string) =>
        useQuery<Board>({
            queryKey: ["board", id],
            queryFn: () => fetchWithAuth(`${API_BASE}/boards/${id}`),
            enabled: !!id,
        });

    // GET /v1/boards/:id/items - Get board items
    const getBoardItems = (id: string) =>
        useQuery<BoardItem[]>({
            queryKey: ["boardItems", id],
            queryFn: () => fetchWithAuth(`${API_BASE}/boards/${id}/items`),
            enabled: !!id,
        });

    const getBoardInsights = (
        id: string,
        options: Omit<UseQueryOptions<BoardInsights>, "queryKey" | "queryFn"> = {}
    ) =>
        useQuery<BoardInsights>({
            queryKey: ["boardInsights", id],
            queryFn: () => fetchWithAuth(`${API_BASE}/boards/${id}/insights`),
            enabled: !!id && (options.enabled ?? true),
            ...options,
        });

    // POST /v1/boards - Create board
    const createBoardMutation = useMutation({
        mutationFn: (data: CreateBoardRequest) =>
            fetchWithAuth(`${API_BASE}/boards`, {
                method: "POST",
                body: JSON.stringify(data),
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["boards"] });
        },
    });

    // DELETE /v1/boards/:id - Delete board
    const deleteBoardMutation = useMutation({
        mutationFn: (boardId: string) =>
            fetchWithAuth(`${API_BASE}/boards/${boardId}`, {
                method: "DELETE",
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["boards"] });
        },
    });

    // POST /v1/boards/:id/items/batch - Add multiple items to board (single request)
    const addToBoardMutation = useMutation({
        mutationFn: async ({
            boardId,
            contentItemIds,
        }: {
            boardId: string;
            contentItemIds: string[];
        }) => {
            // Use batch endpoint for efficiency
            return fetchWithAuth(`${API_BASE}/boards/${boardId}/items/batch`, {
                method: "POST",
                body: JSON.stringify({ content_item_ids: contentItemIds }),
            });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["boards"] }); // Update item counts
            queryClient.invalidateQueries({ queryKey: ["boardItems", variables.boardId] });
        },
    });

    // DELETE /v1/boards/:id/items/:item_id - Remove item from board
    const removeFromBoardMutation = useMutation({
        mutationFn: ({
            boardId,
            contentItemId,
        }: {
            boardId: string;
            contentItemId: string;
        }) =>
            fetchWithAuth(`${API_BASE}/boards/${boardId}/items/${contentItemId}`, {
                method: "DELETE",
            }),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["boards"] });
            queryClient.invalidateQueries({ queryKey: ["boardItems", variables.boardId] });
        },
    });

    const refreshBoardInsightsMutation = useMutation({
        mutationFn: (boardId: string) =>
            fetchWithAuth(`${API_BASE}/boards/${boardId}/insights/refresh`, {
                method: "POST",
            }),
        onSuccess: (_, boardId) => {
            queryClient.invalidateQueries({ queryKey: ["boardInsights", boardId] });
        },
    });

    return {
        // Queries
        boards: boardsQuery.data || [],
        isLoadingBoards: boardsQuery.isLoading,
        boardsError: boardsQuery.error,
        getBoard,
        getBoardItems,
        getBoardInsights,

        // Mutations
        createBoard: createBoardMutation.mutateAsync,
        isCreatingBoard: createBoardMutation.isPending,

        deleteBoard: deleteBoardMutation.mutateAsync,
        isDeletingBoard: deleteBoardMutation.isPending,

        addToBoard: addToBoardMutation.mutateAsync,
        isAddingToBoard: addToBoardMutation.isPending,

        removeFromBoard: removeFromBoardMutation.mutateAsync,
        isRemovingFromBoard: removeFromBoardMutation.isPending,

        refreshBoardInsights: refreshBoardInsightsMutation.mutateAsync,
        isRefreshingInsights: refreshBoardInsightsMutation.isPending,

        // Refetch
        refetchBoards: () => queryClient.invalidateQueries({ queryKey: ["boards"] }),
    };
}
