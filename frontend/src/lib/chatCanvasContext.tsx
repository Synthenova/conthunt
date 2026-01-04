"use client";

import { createContext, useContext } from "react";

interface ChatCanvasContextValue {
    resultsMap: Record<string, any[]>;
    activeSearchId: string | null;
    setActiveSearchId: (id: string | null) => void;
}

export const ChatCanvasContext = createContext<ChatCanvasContextValue | null>(null);

export function useChatCanvasContext() {
    return useContext(ChatCanvasContext);
}
