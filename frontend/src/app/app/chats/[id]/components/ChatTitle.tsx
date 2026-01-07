
import { useRef } from "react";
import { Check, Trash, X, Pencil, Search } from "lucide-react";
import { SearchIconHandle, SearchIcon } from "@/components/ui/search";

interface ChatTitleProps {
    activeChatTitle: string;
    isEditingTitle: boolean;
    editingTitle: string;
    setEditingTitle: (value: string) => void;
    startTitleEdit: () => void;
    cancelTitleEdit: () => void;
    commitTitleEdit: () => void;
    onDeleteChat: () => void;
    resultCount?: number;
}

export function ChatTitle({
    activeChatTitle,
    isEditingTitle,
    editingTitle,
    setEditingTitle,
    startTitleEdit,
    cancelTitleEdit,
    commitTitleEdit,
    onDeleteChat,
    resultCount
}: ChatTitleProps) {
    const searchIconRef = useRef<SearchIconHandle>(null);

    return (
        <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between">
                <div
                    className="flex items-center gap-3 group cursor-default"
                    onMouseEnter={() => searchIconRef.current?.startAnimation()}
                    onMouseLeave={() => searchIconRef.current?.stopAnimation()}
                >
                    <SearchIcon
                        ref={searchIconRef}
                        size={20}
                        className="text-muted-foreground group-hover:text-white transition-colors"
                    />
                    <div className="flex items-center gap-2">
                        {isEditingTitle ? (
                            <>
                                <input
                                    autoFocus
                                    value={editingTitle}
                                    onChange={(event) => setEditingTitle(event.target.value)}
                                    onKeyDown={(event) => {
                                        if (event.key === 'Enter') {
                                            event.preventDefault();
                                            commitTitleEdit();
                                        }
                                        if (event.key === 'Escape') {
                                            event.preventDefault();
                                            cancelTitleEdit();
                                        }
                                    }}
                                    onBlur={commitTitleEdit}
                                    size={Math.max(1, editingTitle.length)}
                                    className="bg-transparent text-xl font-medium text-white outline-none border-b border-white/50 border-radius-md"
                                />
                                <button
                                    type="button"
                                    onMouseDown={(e) => {
                                        e.preventDefault();
                                        commitTitleEdit();
                                    }}
                                    className="text-white/60 hover:text-white transition-colors"
                                    aria-label="Save"
                                >
                                    <Check size={14} />
                                </button>
                                <button
                                    type="button"
                                    onMouseDown={(e) => {
                                        e.preventDefault();
                                        onDeleteChat();
                                    }}
                                    className="text-white/60 hover:text-white transition-colors"
                                    aria-label="Delete chat"
                                >
                                    <Trash size={14} />
                                </button>
                                <button
                                    type="button"
                                    onMouseDown={(e) => {
                                        e.preventDefault();
                                        cancelTitleEdit();
                                    }}
                                    className="text-white/60 hover:text-white transition-colors"
                                    aria-label="Cancel"
                                >
                                    <X size={14} />
                                </button>
                            </>
                        ) : (
                            <>
                                <h1 className="text-xl font-medium text-white">{activeChatTitle}</h1>
                                <button
                                    type="button"
                                    onClick={startTitleEdit}
                                    className="text-white/60 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
                                    aria-label="Rename chat"
                                >
                                    <Pencil size={14} />
                                </button>
                            </>
                        )}
                    </div>
                </div>
                {resultCount !== undefined && (
                    <div className="text-sm text-muted-foreground">
                        Showing {resultCount} results
                    </div>
                )}
            </div>
        </div>
    );
}
