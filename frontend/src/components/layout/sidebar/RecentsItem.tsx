"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from "framer-motion";
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface RecentsItemProps {
    label: string;
    icon?: LucideIcon | any;
    active?: boolean;
    onClick?: () => void;
    href?: string;
}

export const RecentsItem = ({ label, icon: Icon, active, onClick, href }: RecentsItemProps) => {
    const content = (
        <>
            <div className="relative z-10 flex items-center gap-3">
                {Icon && <Icon size={16} className={cn("shrink-0 transition-colors opacity-70", active ? "text-white opacity-100" : "group-hover:text-gray-200 group-hover:opacity-100")} />}
                <span className={cn("text-sm truncate font-medium transition-colors", active ? "text-white" : "text-gray-400 group-hover:text-gray-200")}>
                    {label}
                </span>
            </div>
            {active && (
                <motion.div
                    layoutId="recent-item-pill"
                    className="absolute inset-0 rounded-lg bg-white/5 border border-white/5 shadow-sm"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
            )}
        </>
    );

    const containerClasses = cn(
        "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left group relative"
    );

    if (onClick) {
        return (
            <button onClick={onClick} className={containerClasses}>
                {content}
            </button>
        );
    }

    if (href) {
        return (
            <Link href={href} className={containerClasses}>
                {content}
            </Link>
        );
    }

    return null;
};
