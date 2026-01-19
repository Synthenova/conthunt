"use client";

import React, { useState, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ImagePlus, X, Rocket, Loader2, Bug } from "lucide-react";
import Image from 'next/image';
import { toast } from 'sonner';

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function FeedbackModal({ isOpen, onClose }: FeedbackModalProps) {
    const [message, setMessage] = useState("");
    const [images, setImages] = useState<File[]>([]);
    const [previews, setPreviews] = useState<string[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files);
            setImages(prev => [...prev, ...newFiles]);

            // Generate previews
            const newPreviews = newFiles.map(file => URL.createObjectURL(file));
            setPreviews(prev => [...prev, ...newPreviews]);
        }
    };

    const removeImage = (index: number) => {
        setImages(prev => prev.filter((_, i) => i !== index));
        setPreviews(prev => {
            // Revoke object URL to avoid memory leaks
            URL.revokeObjectURL(prev[index]);
            return prev.filter((_, i) => i !== index);
        });
    };

    const handleSubmit = async () => {
        if (!message.trim()) {
            toast.error("Please enter a message describing the issue/feedback.");
            return;
        }

        setIsSubmitting(true);
        try {
            const formData = new FormData();
            formData.append("message", message);
            images.forEach(image => {
                formData.append("images", image);
            });

            const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/v1/feedback`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Failed to send feedback");
            }

            toast.success("Feedback sent successfully! Thank you.");
            handleClose();
        } catch (error) {
            console.error(error);
            toast.error("Something went wrong. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClose = () => {
        setMessage("");
        setImages([]);
        previews.forEach(url => URL.revokeObjectURL(url));
        setPreviews([]);
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[500px] bg-[#0A0A0A] border-[#1F1F1F] text-gray-100">
                <DialogHeader>
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-orange-500/10 border border-orange-500/20">
                            <Bug className="w-5 h-5 text-orange-500" />
                        </div>
                        <DialogTitle>Report a Bug / Feedback</DialogTitle>
                    </div>
                    <DialogDescription className="text-gray-400">
                        Found a bug or have a suggestion? Let us know!
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-2">
                    <Textarea
                        placeholder="Describe the issue or idea..."
                        className="bg-[#121212] border-white/10 text-gray-200 min-h-[120px] focus-visible:ring-orange-500/50 resize-none"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                    />

                    {/* Image Previews */}
                    {previews.length > 0 && (
                        <div className="flex gap-2 overflow-x-auto py-2">
                            {previews.map((src, idx) => (
                                <div key={idx} className="relative w-16 h-16 shrink-0 rounded-md border border-white/10 overflow-hidden group">
                                    <Image src={src} alt="Preview" fill className="object-cover" />
                                    <button
                                        onClick={() => removeImage(idx)}
                                        className="absolute top-0 right-0 bg-black/60 p-0.5 rounded-bl-md hover:bg-red-500/80 transition-colors"
                                    >
                                        <X size={12} className="text-white" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="flex items-center justify-between">
                        <div
                            onClick={() => fileInputRef.current?.click()}
                            className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-200 cursor-pointer transition-colors"
                        >
                            <ImagePlus size={16} />
                            <span>Add Screenshots</span>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                multiple
                                accept="image/*"
                                onChange={handleFileChange}
                            />
                        </div>
                        <span className="text-xs text-gray-500">{message.length}/1000</span>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="ghost" onClick={handleClose} disabled={isSubmitting} className="hover:bg-white/5 hover:text-white">
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={isSubmitting}
                        className="bg-orange-600 hover:bg-orange-700 text-white gap-2"
                    >
                        {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />}
                        Send Report
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
