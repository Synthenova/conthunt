"use client";

import { useCallback, useEffect } from "react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageLightboxProps {
    isOpen: boolean;
    onClose: () => void;
    imageUrl: string | null;
    alt?: string;
}

export function ImageLightbox({ isOpen, onClose, imageUrl, alt = "Image" }: ImageLightboxProps) {
    // Close on Escape key
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape" && isOpen) {
                onClose();
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, onClose]);

    if (!imageUrl) return null;

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent
                className={cn(
                    "max-w-[90vw] max-h-[90vh] p-0 border-none bg-transparent",
                    "flex items-center justify-center"
                )}
                showCloseButton={false}
            >
                <VisuallyHidden>
                    <DialogTitle>Image Preview</DialogTitle>
                </VisuallyHidden>

                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-50 p-2 rounded-full bg-black/60 hover:bg-black/80 text-white transition-colors"
                    aria-label="Close"
                >
                    <X className="h-5 w-5" />
                </button>

                {/* Image */}
                <div
                    className="relative w-full h-full flex items-center justify-center"
                    onClick={onClose}
                >
                    <img
                        src={imageUrl}
                        alt={alt}
                        className="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
            </DialogContent>
        </Dialog>
    );
}
