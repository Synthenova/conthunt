import { cn } from '@/lib/utils';
import { Play } from 'lucide-react';
import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";

interface MediaChipData {
    id: string;
    title: string;
    platform: string;
    thumbnail_url?: string;
}

interface StackedMediaChipsProps {
    chips: MediaChipData[];
    onChipClick?: (id: string, platform: string) => void;
}

function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes("tiktok")) return FaTiktok;
    if (normalized.includes("instagram")) return FaInstagram;
    if (normalized.includes("youtube")) return FaYoutube;
    if (normalized.includes("pinterest")) return FaPinterest;
    return FaGlobe;
}

export function StackedMediaChips({ chips, onChipClick }: StackedMediaChipsProps) {
    if (!chips.length) return null;

    return (
        <div className="group flex flex-wrap-reverse items-end justify-end w-full mb-1 gap-1 transition-all duration-300">
            {/* 
               Stack Effect:
               - Default: Negative margins cause overlap.
               - Hover: Margins reset to 0, gap takes over for grid layout.
            */}
            {chips.map((chip, index) => {
                const PlatformIcon = getPlatformIcon(chip.platform);

                return (
                    <div
                        key={chip.id}
                        onClick={() => onChipClick?.(chip.id, chip.platform)}
                        className={cn(
                            "relative h-16 w-12 shrink-0 rounded-lg overflow-hidden border border-white/10 bg-black/40 cursor-pointer transition-all duration-300 ease-out shadow-lg",
                            // Stack Effect:
                            // We use -ml-[40px] to creating the stacking overlap.
                            // group-hover:ml-0 removes overlap, allowing gap-1 to take effect.
                            index !== 0 && "-ml-[40px] group-hover:ml-0",

                            // Visuals
                            "hover:z-20 hover:scale-105 hover:ring-1 hover:ring-white/20"
                        )}
                        style={{
                            // Default stacking order: later items on top
                            zIndex: index
                        }}
                    >
                        {chip.thumbnail_url ? (
                            <img
                                src={chip.thumbnail_url}
                                alt={chip.title}
                                className="h-full w-full object-cover"
                            />
                        ) : (
                            <div className="absolute inset-0 flex items-center justify-center bg-white/5">
                                {PlatformIcon ? (
                                    <PlatformIcon className="h-6 w-6 text-muted-foreground" />
                                ) : (
                                    <Play className="h-6 w-6 text-muted-foreground opacity-50" />
                                )}
                            </div>
                        )}

                        {/* Mini Platform Icon */}
                        {PlatformIcon && (
                            <div className="absolute bottom-1 right-1 rounded-full bg-black/60 p-0.5">
                                <PlatformIcon className="h-2.5 w-2.5 text-white" />
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
