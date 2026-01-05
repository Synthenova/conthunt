"use client";

import { LayoutDashboard, Search, ImagePlus, Loader2, X } from 'lucide-react';
import type { ContextChip, ImageChip, ChatChip } from './types';
import { truncateText, getPlatformIcon } from './utils';
import { CHIP_TITLE_LIMIT } from './constants';

interface ChipListProps {
    chips: ContextChip[];
    imageChips: ImageChip[];
    onRemoveChip: (chip: ContextChip) => void;
    onRemoveImageChip: (chipId: string) => void;
}

export function ChipList({ chips, imageChips, onRemoveChip, onRemoveImageChip }: ChipListProps) {
    const allChips: ChatChip[] = [...chips, ...imageChips];

    if (allChips.length === 0) return null;

    return (
        <div className="flex flex-nowrap overflow-x-auto scrollbar-none gap-2 px-2 pt-2">
            {allChips.map((chip) => {
                const PlatformIcon = chip.type === 'media' ? getPlatformIcon(chip.platform) : null;
                return (
                    <span
                        key={`${chip.type}-${chip.id}`}
                        className="inline-flex shrink-0 items-center gap-1 rounded-full bg-background/60 px-2.5 py-1 text-xs font-medium text-foreground/90 ring-1 ring-white/10"
                    >
                        {chip.type === 'board' && (
                            <>
                                <LayoutDashboard className="h-3.5 w-3.5 text-muted-foreground" />
                                <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                            </>
                        )}
                        {chip.type === 'chat' && (
                            <>
                                <LayoutDashboard className="h-3.5 w-3.5 text-muted-foreground" />
                                <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                            </>
                        )}
                        {chip.type === 'search' && (
                            <>
                                <Search className="h-3.5 w-3.5 text-muted-foreground" />
                                <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                            </>
                        )}
                        {chip.type === 'image' && (
                            <div className="relative h-4 w-4 shrink-0 rounded overflow-hidden">
                                {chip.status === 'uploading' ? (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                                    </div>
                                ) : chip.url ? (
                                    <img
                                        src={chip.url}
                                        alt={chip.fileName}
                                        className="h-full w-full object-cover"
                                    />
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <ImagePlus className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                )}
                            </div>
                        )}
                        {chip.type === 'media' && PlatformIcon && (
                            <>
                                <PlatformIcon className="text-[12px]" />
                                <span className="truncate" title={chip.title}>
                                    {truncateText(chip.title, CHIP_TITLE_LIMIT)}
                                </span>
                            </>
                        )}
                        {chip.type === 'image' ? (
                            <button
                                type="button"
                                onClick={() => onRemoveImageChip(chip.id)}
                                className="rounded-full hover:text-foreground"
                                aria-label={`Remove ${chip.fileName}`}
                            >
                                <X className="h-3 w-3" />
                            </button>
                        ) : !chip.locked && (
                            <button
                                type="button"
                                onClick={() => onRemoveChip(chip)}
                                className="rounded-full hover:text-foreground"
                                aria-label={`Remove ${chip.label}`}
                            >
                                <X className="h-3 w-3" />
                            </button>
                        )}
                    </span>
                );
            })}
        </div>
    );
}
