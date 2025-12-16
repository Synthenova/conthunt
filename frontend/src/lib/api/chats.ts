import { auth } from "@/lib/firebaseClient";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeaders() {
    const user = auth.currentUser;
    const token = user ? await user.getIdToken() : null;
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
    if (!res.ok) {
        if (res.status === 401) throw new Error("Not authenticated");
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "API request failed");
    }
    return res.json();
}

export const api = {
    getChats: async () => {
        const headers = await getAuthHeaders();
        // If no token, decide if we want to return empty or throw. 
        // The hook logic currently implies empty if no token, 
        // but usually getAuthHeaders returns empty object if no token, 
        // which might cause 401 on server.
        // Let's rely on the server 401 check or check token existence here.
        if (!headers.Authorization) return [];

        const res = await fetch(`${API_URL}/v1/chats`, { headers });
        return handleResponse<any[]>(res);
    },

    getMessages: async (chatId: string) => {
        const headers = await getAuthHeaders();
        if (!headers.Authorization) throw new Error("Please log in to view messages");

        const res = await fetch(`${API_URL}/v1/chats/${chatId}/messages`, { headers });
        const data = await handleResponse<{ messages: any[] }>(res);
        return data.messages;
    },

    createChat: async (title: string) => {
        const headers = await getAuthHeaders();
        if (!headers.Authorization) throw new Error("Please log in to create a chat");

        const res = await fetch(`${API_URL}/v1/chats`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ title }),
        });
        return handleResponse<{ id: string; title: string }>(res);
    },

    deleteChat: async (chatId: string) => {
        const headers = await getAuthHeaders();
        if (!headers.Authorization) throw new Error("Not authenticated");

        const res = await fetch(`${API_URL}/v1/chats/${chatId}`, {
            method: "DELETE",
            headers,
        });
        if (!res.ok) throw new Error("Failed to delete chat");
    },

    sendMessage: async (chatId: string, message: string) => {
        const headers = await getAuthHeaders();
        if (!headers.Authorization) throw new Error("Please log in to send messages");

        const res = await fetch(`${API_URL}/v1/chats/${chatId}/send`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
        // This is fire-and-forget/optimistic often, but good to check OK
        if (!res.ok) throw new Error("Failed to send message");
    },

    getStreamUrl: (chatId: string) => `${API_URL}/v1/chats/${chatId}/stream`,

    getToken: async () => {
        const user = auth.currentUser;
        return user ? await user.getIdToken() : null;
    }
};
