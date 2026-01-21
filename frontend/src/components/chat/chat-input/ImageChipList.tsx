"use client";

import { Loader2, X, Play } from 'lucide-react';
import type { ImageChip, MediaChip } from './types';
import { getPlatformIcon } from './utils';

interface ImageChipListProps {
    chips: (ImageChip | MediaChip)[];
    onRemoveChip: (chipId: string, type: 'image' | 'media') => void;
}

export function ImageChipList({ chips, onRemoveChip }: ImageChipListProps) {
    if (chips.length === 0) return null;

    return (
        <div className="flex flex-wrap-reverse items-end justify-end gap-1 w-full max-w-[90%] mx-auto pointer-events-auto py-[2px] mb-0.5">
            {chips.map((chip) => {
                const isImage = chip.type === 'image';
                const isMedia = chip.type === 'media';

                // Determine thumbnail URL
                let thumbUrl = '';
                if (isImage) thumbUrl = chip.url || '';
                if (isMedia) thumbUrl = chip.thumbnail_url || '';

                // Determine Alt text
                const altText = isImage ? chip.fileName : chip.title;

                // Platform Icon for Media
                const PlatformIcon = isMedia ? getPlatformIcon(chip.platform) : null;

                return (
                    <div
                        key={`${chip.type}-${chip.id}`}
                        className="relative h-16 w-12 shrink-0 rounded-lg overflow-hidden border border-white/10 group bg-black/40"
                    >
                        {isImage && chip.status === 'uploading' ? (
                            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                                <Loader2 className="h-4 w-4 animate-spin text-white/70" />
                            </div>
                        ) : thumbUrl ? (
                            <img
                                src={thumbUrl}
                                alt={altText}
                                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
                            />
                        ) : (
                            // Fallback if no thumbnail
                            <div className="absolute inset-0 flex items-center justify-center bg-white/5">
                                {PlatformIcon ? (
                                    <PlatformIcon className="h-6 w-6 text-muted-foreground" />
                                ) : (
                                    <Play className="h-6 w-6 text-muted-foreground opacity-50" />
                                )}
                            </div>
                        )}

                        {/* Remove Button Overlay */}
                        <div className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                                type="button"
                                onClick={() => onRemoveChip(chip.id, chip.type)}
                                className="rounded-full bg-white/10 p-1 text-white hover:bg-red-500/80 transition-colors"
                                aria-label={`Remove ${altText}`}
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>

                        {/* Mini Platform Icon Bottom Right for Media */}
                        {isMedia && PlatformIcon && (
                            <div className="absolute bottom-1 right-1 rounded-full bg-black/60 p-0.5">
                                <PlatformIcon className="h-3 w-3 text-white" />
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
