"use client";

import React from 'react';
import { motion, HTMLMotionProps, AnimatePresence } from 'framer-motion';

// Orchestrates the children appearing one by one
export const StaggerContainer: React.FC<HTMLMotionProps<"div">> = ({ children, className, ...props }) => {
    return (
        <motion.div
            initial="hidden"
            animate="show"
            exit="hidden"
            variants={{
                hidden: { opacity: 0 },
                show: {
                    opacity: 1,
                    transition: {
                        staggerChildren: 0.05, // Snappier delay
                        delayChildren: 0.1,
                    }
                }
            }}
            className={className}
            {...props}
        >
            {children}
        </motion.div>
    );
};

// The individual item that slides up and fades in
export const StaggerItem: React.FC<HTMLMotionProps<"div">> = ({ children, className, ...props }) => {
    return (
        <motion.div
            variants={{
                hidden: { opacity: 0, y: 10, scale: 0.98 },
                show: {
                    opacity: 1,
                    y: 0,
                    scale: 1,
                    transition: {
                        type: "spring",
                        stiffness: 260,
                        damping: 20
                    }
                }
            }}
            className={className}
            {...props}
        >
            {children}
        </motion.div>
    );
};

// Simple fade in for singular blocks (headers, large panels)
export const FadeIn: React.FC<HTMLMotionProps<"div"> & { delay?: number }> = ({ children, delay = 0, className, ...props }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.25, 0.25, 0, 1], delay }}
            className={className}
            {...props}
        >
            {children}
        </motion.div>
    );
};

export { AnimatePresence };
