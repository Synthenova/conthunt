"use client";

import React, { useRef } from 'react';
import Link from 'next/link';
import { motion } from "framer-motion";
import { cn } from '@/lib/utils';

interface NavItemProps {
    icon: any;
    label: string;
    path: string;
    active: boolean;
    isCollapsed: boolean;
    onModalClick?: () => void;
}

export const NavItem = ({ icon: Icon, label, path, active, isCollapsed, onModalClick }: NavItemProps) => {
    const isModalNav = label === 'Chats' || label === 'Searches';
    const iconRef = useRef<any>(null);

    const handleMouseEnter = () => {
        iconRef.current?.startAnimation?.();
    };

    const handleMouseLeave = () => {
        iconRef.current?.stopAnimation?.();
    };

    const content = (
        <>
            <div className="relative z-10 flex items-center gap-3">
                <Icon
                    ref={iconRef}
                    size={20}
                    className={cn("transition-colors shrink-0", active ? "text-white" : "group-hover:text-gray-200")}
                />
                {!isCollapsed && (
                    <span className="font-medium text-sm whitespace-nowrap overflow-hidden transition-all duration-300 origin-left">
                        {label}
                    </span>
                )}
            </div>
            {active && (
                <motion.div
                    layoutId="nav-pill"
                    className="absolute inset-0 rounded-full glass-pill"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
            )}
        </>
    );

    const classes = cn(
        "flex items-center transition-all duration-200 group relative",
        isCollapsed
            ? "justify-center w-12 h-12 rounded-full mx-auto"
            : "w-full space-x-3 px-3 py-2.5 rounded-full",
        active
            ? "text-white"
            : "text-gray-400 hover:text-gray-200"
    );

    if (isModalNav) {
        return (
            <button
                type="button"
                onClick={onModalClick}
                className={classes}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
            >
                {content}
            </button>
        );
    }

    return (
        <Link
            href={path}
            className={classes}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            {content}
        </Link>
    );
};
