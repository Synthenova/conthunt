"use client";

import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface AsyncImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
    src: string;
    className?: string;
}

export function AsyncImage({ src, className, alt, ...props }: AsyncImageProps) {
    const [loaded, setLoaded] = useState(false);
    const imgRef = useRef<HTMLImageElement>(null);

    useEffect(() => {
        setLoaded(false);
    }, [src]);

    useEffect(() => {
        if (imgRef.current?.complete) {
            setLoaded(true);
        }
    }, [src]);

    return (
        <div className={cn("relative overflow-hidden", className)}>
            <img
                ref={imgRef}
                src={src}
                alt={alt || ""}
                className={cn(
                    "w-full h-full object-cover transition-all duration-700",
                    loaded ? "opacity-100 scale-100 blur-0" : "opacity-0 scale-105 blur-lg"
                )}
                onLoad={() => setLoaded(true)}
                {...props}
            />
            {!loaded && (
                <div className="absolute inset-0 bg-white/5 animate-pulse" />
            )}
        </div>
    );
}
