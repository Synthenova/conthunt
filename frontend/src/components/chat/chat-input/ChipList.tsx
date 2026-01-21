"use client";

import { LayoutDashboard, Search } from 'lucide-react';
import type { ContextChip, ChatChip } from './types';
import { truncateText, getPlatformIcon } from './utils';
import { CHIP_TITLE_LIMIT } from './constants';

interface ChipListProps {
    chips: ContextChip[];
    onRemoveChip: (chip: ContextChip) => void;
}

export function ChipList({ chips, onRemoveChip }: ChipListProps) {
    if (chips.length === 0) return null;

    return (
        <div className="flex flex-nowrap overflow-x-auto scrollbar-none gap-2 px-2 pt-2">
            {chips.map((chip) => {
                const PlatformIcon = chip.type === 'media' ? getPlatformIcon(chip.platform) : null;
                return (
                    <span
                        key={`${chip.type}-${chip.id}`}
                        className="inline-flex shrink-0 items-center gap-1 rounded-full bg-[#b7b7b7] px-2.5 py-1 text-xs font-medium text-black ring-1 ring-white/10 -translate-y-0.5"
                    >
                        {chip.type === 'board' && (
                            <>
                                <LayoutDashboard className="h-3.5 w-3.5 text-black/60" />
                                <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                            </>
                        )}
                        {chip.type === 'chat' && (
                            <>
                                <LayoutDashboard className="h-3.5 w-3.5 text-black/60" />
                                <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                            </>
                        )}
                        {chip.type === 'search' && (
                            <>
                                <Search className="h-3.5 w-3.5 text-black/60" />
                                <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                            </>
                        )}
                        {chip.type === 'media' && PlatformIcon && (
                            <>
                                <PlatformIcon className="text-[12px] text-black/60" />
                                <span className="truncate" title={chip.title}>
                                    {truncateText(chip.title, CHIP_TITLE_LIMIT)}
                                </span>
                            </>
                        )}
                        {!chip.locked && (
                            <button
                                type="button"
                                onClick={() => onRemoveChip(chip)}
                                className="rounded-full hover:text-black"
                                aria-label={`Remove ${chip.label}`}
                            >
                                <X className="h-3 w-3 text-black/60" />
                            </button>
                        )}
                    </span>
                );
            })}
        </div>
    );
}

// Helper X icon was missing in previous import if we removed ImagePlus etc.
// Re-adding X to imports if it wasn't there, but it was.
// Cleaned up imports.
import { X } from 'lucide-react';
