import React from "react";
import { cn } from "@/lib/utils";
import { HTMLMotionProps, motion } from "framer-motion";

interface BoardGlassCardProps extends HTMLMotionProps<"div"> {
    children: React.ReactNode;
}

export function BoardGlassCard({
    children,
    className,
    ...props
}: BoardGlassCardProps) {
    return (
        <motion.div
            className={cn(
                "relative rounded-3xl overflow-hidden backdrop-blur-xl transition-all duration-75 group",
                className
            )}
            style={{
                background: "linear-gradient(180deg, rgba(255, 255, 255, 0.07) 0%, rgba(212, 212, 212, 0.04) 34%, rgba(153, 153, 153, 0) 55%, rgba(212, 212, 212, 0.04) 77%, rgba(255, 255, 255, 0.07) 100%)",
                boxShadow: "0 4px 30px rgba(0, 0, 0, 0.1)",
            }}
            whileHover={{ y: -4, scale: 1.01 }}
            transition={{ duration: 0.05, ease: "easeOut" }}
            {...props}
        >
            {/* Gradient Border Pseudo-element */}
            <div
                className="absolute inset-0 rounded-3xl pointer-events-none z-20"
                style={{
                    padding: "1px",
                    background: "linear-gradient(170deg, rgba(128, 128, 128, 0.4) 0%, rgba(0, 0, 0, 0) 40%, rgba(0, 0, 0, 0) 60%, rgba(128, 128, 128, 0.4) 100%)",
                    WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                    mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                    WebkitMaskComposite: "xor",
                    maskComposite: "exclude",
                }}
            />

            {/* Content Container */}
            <div className="relative z-10 w-full h-full">
                {children}
            </div>

            {/* Subtle internal shine on hover */}
            <div
                className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-100 pointer-events-none z-0"
            />

        </motion.div>
    );
}
