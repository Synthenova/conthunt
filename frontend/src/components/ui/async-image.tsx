"use client";

import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface AsyncImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
    src: string;
    className?: string;
}

export function AsyncImage({ src, className, alt, ...props }: AsyncImageProps) {
    const [loaded, setLoaded] = useState(false);
    const [currentSrc, setCurrentSrc] = useState<string>(src);
    const [isConverting, setIsConverting] = useState(false);
    const [error, setError] = useState(false);
    const imgRef = useRef<HTMLImageElement>(null);

    // Heuristic detection based on URL extension
    const isKnownHeic = src?.toLowerCase().endsWith('.heic');

    useEffect(() => {
        let active = true;
        let objectUrl: string | null = null;

        const loadHost = async () => {
            setLoaded(false);
            setIsConverting(false);
            setError(false);

            // Optimization: If we KNOW it's heic from extension, convert immediately
            if (isKnownHeic) {
                await processHeic(src);
            } else {
                setCurrentSrc(src);
            }
        };

        const processHeic = async (url: string) => {
            if (!url) return;
            try {
                setIsConverting(true);
                const heic2any = (await import('heic2any')).default;

                const response = await fetch(url);
                if (!response.ok) throw new Error("Fetch failed");
                const blob = await response.blob();

                const convertedBlob = await heic2any({
                    blob,
                    toType: "image/jpeg",
                    quality: 0.8
                });

                if (!active) return;
                const singleBlob = Array.isArray(convertedBlob) ? convertedBlob[0] : convertedBlob;
                objectUrl = URL.createObjectURL(singleBlob);
                setCurrentSrc(objectUrl);
            } catch (error) {
                console.error("[AsyncImage] HEIC conversion failed:", error);
                if (active && !isKnownHeic) setError(true);
            } finally {
                if (active) setIsConverting(false);
            }
        };

        // If it's NOT a known HEIC, we just set the src.
        if (!isKnownHeic) {
            setCurrentSrc(src);
        } else {
            loadHost();
        }

        return () => {
            active = false;
            // Clean up object URLs when unmounting or changing src
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [src, isKnownHeic]);

    const handleError = async () => {
        // Prevent infinite loops if fallback also fails or during conversion
        if (isConverting || isKnownHeic || currentSrc.startsWith("blob:")) {
            setError(true);
            return;
        }

        console.log("[AsyncImage] Image load failed. Checking for hidden HEIC...", src);
        setIsConverting(true);

        try {
            const response = await fetch(src);
            if (!response.ok) {
                setError(true);
                return;
            }

            const blob = await response.blob();

            // MAGIC BYTES CHECK: Check for 'ftyp' signal at offset 4
            // HEIC/HEIF usually starts with 00 00 00 [width] 66 74 79 70 ...
            const buffer = await blob.slice(0, 16).arrayBuffer();
            const arr = new Uint8Array(buffer);

            // Check for 'ftyp' at index 4 (0x66, 0x74, 0x79, 0x70)
            const isFtyp = arr[4] === 0x66 && arr[5] === 0x74 && arr[6] === 0x79 && arr[7] === 0x70;

            if (isFtyp) {
                console.log("[AsyncImage] Detected hidden HEIC (ftyp signature). Converting...");
                const heic2any = (await import('heic2any')).default;
                const convertedBlob = await heic2any({
                    blob,
                    toType: "image/jpeg",
                    quality: 0.8
                });

                const singleBlob = Array.isArray(convertedBlob) ? convertedBlob[0] : convertedBlob;
                const newUrl = URL.createObjectURL(singleBlob);
                setCurrentSrc(newUrl);
            } else {
                setError(true);
            }
        } catch (e) {
            console.error("[AsyncImage] Fallback check failed:", e);
            setError(true);
        } finally {
            setIsConverting(false);
        }
    };

    return (
        <div className={cn("relative overflow-hidden", className)}>
            <img
                ref={imgRef}
                src={currentSrc}
                alt={alt || ""}
                className={cn(
                    "w-full h-full object-cover transition-all duration-700",
                    loaded && !error ? "opacity-100 scale-100 blur-0" : "opacity-0 scale-105 blur-lg"
                )}
                onLoad={() => setLoaded(true)}
                onError={handleError}
                {...props}
            />
            {(!loaded && !error) && (
                <div className={cn(
                    "absolute inset-0 bg-white/5",
                    isConverting ? "animate-pulse bg-blue-500/10" : "animate-pulse" // Visual hint for debug
                )} />
            )}
            {error && (
                <div className="absolute inset-0 bg-zinc-900 flex items-center justify-center text-zinc-700 text-xs">
                    Error
                </div>
            )}
        </div>
    );
}
