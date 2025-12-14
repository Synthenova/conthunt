"use client";

import { MediaCard } from "./MediaCard";
import { useSearchStore } from "@/lib/store";
import { Check } from "lucide-react";

interface SelectableMediaCardProps {
    item: any;
    platform: string;
}

export function SelectableMediaCard({ item, platform }: SelectableMediaCardProps) {
    const { selectedItems, toggleItemSelection } = useSearchStore();
    const isSelected = selectedItems.includes(item.id);

    const handleSelect = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        toggleItemSelection(item.id);
    };

    return (
        <div className="relative group/select">
            {/* Selection Checkbox */}
            <button
                onClick={handleSelect}
                className={`
                    absolute top-2 left-2 z-20 h-6 w-6 rounded-md border-2 
                    flex items-center justify-center transition-all duration-200
                    ${isSelected
                        ? 'bg-primary border-primary text-white scale-100'
                        : 'bg-black/40 border-white/50 text-transparent hover:border-white hover:bg-black/60 scale-90 group-hover/select:scale-100'
                    }
                    ${isSelected ? 'opacity-100' : 'opacity-0 group-hover/select:opacity-100'}
                `}
            >
                <Check className="h-4 w-4" strokeWidth={3} />
            </button>

            {/* Selection Glow Effect */}
            {isSelected && (
                <div className="absolute inset-0 rounded-xl ring-2 ring-primary ring-offset-2 ring-offset-background z-10 pointer-events-none" />
            )}

            {/* Original Media Card */}
            <MediaCard item={item} platform={platform} />
        </div>
    );
}
