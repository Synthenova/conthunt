"use client";

import { ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MODEL_OPTIONS } from './constants';

interface ModelSelectorProps {
    selectedModel: string;
    onModelChange: (model: string) => void;
}

export function ModelSelector({ selectedModel, onModelChange }: ModelSelectorProps) {
    const selectedModelLabel = MODEL_OPTIONS.find(
        (option) => option.value === selectedModel
    )?.label || selectedModel;

    return (
        <DropdownMenu modal={false}>
            <DropdownMenuTrigger asChild>
                <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 gap-1 rounded-full px-2 text-xs text-foreground/80"
                    onClick={(event) => event.stopPropagation()}
                >
                    <span className="max-w-[140px] truncate">{selectedModelLabel}</span>
                    <ChevronDown className="h-3.5 w-3.5" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="bg-zinc-900 border-white/10 text-white">
                <DropdownMenuRadioGroup
                    value={selectedModel}
                    onValueChange={onModelChange}
                >
                    {MODEL_OPTIONS.map((option) => (
                        <DropdownMenuRadioItem
                            key={option.value}
                            value={option.value}
                            className="focus:bg-white/10 focus:text-white"
                        >
                            {option.label}
                        </DropdownMenuRadioItem>
                    ))}
                </DropdownMenuRadioGroup>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
