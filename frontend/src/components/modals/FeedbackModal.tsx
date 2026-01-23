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
            <DialogContent className="bg-[#0f0f0f] border border-white/10 text-gray-200 p-0 gap-0 overflow-hidden shadow-2xl rounded-3xl sm:max-w-xl w-full outline-none transition-all duration-200">
                <div className="p-6 pb-2">
                    <DialogHeader>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2.5 rounded-xl bg-white/5 border border-white/10">
                                <Bug className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <DialogTitle className="text-xl font-semibold text-white">Report a Bug / Feedback</DialogTitle>
                                <DialogDescription className="text-zinc-400 mt-1">
                                    Found a bug or have a suggestion? Let us know!
                                </DialogDescription>
                            </div>
                        </div>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <Textarea
                            placeholder="Describe the issue or idea..."
                            className="bg-[#151515] border-white/10 text-gray-200 min-h-[160px] focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-white/10 resize-none rounded-xl p-4 placeholder:text-zinc-600 text-base"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                        />

                        {/* Image Previews */}
                        {previews.length > 0 && (
                            <div className="flex gap-2 overflow-x-auto py-2">
                                {previews.map((src, idx) => (
                                    <div key={idx} className="relative w-16 h-16 shrink-0 rounded-lg border border-white/10 overflow-hidden group">
                                        <Image src={src} alt="Preview" fill className="object-cover" />
                                        <button
                                            onClick={() => removeImage(idx)}
                                            className="absolute top-0 right-0 bg-black/60 p-1 rounded-bl-lg hover:bg-red-500/80 transition-colors backdrop-blur-sm"
                                        >
                                            <X size={12} className="text-white" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="flex items-center justify-between px-1">
                            <div
                                onClick={() => fileInputRef.current?.click()}
                                className="flex items-center gap-2 text-xs font-medium text-zinc-400 hover:text-white cursor-pointer transition-colors px-2 py-1.5 rounded-lg hover:bg-white/5"
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
                            <span className="text-[10px] font-mono text-zinc-600">{message.length}/1000</span>
                        </div>
                    </div>

                    <DialogFooter className="pt-2 mt-0">
                        <Button
                            variant="ghost"
                            onClick={handleClose}
                            disabled={isSubmitting}
                            className="hover:bg-white/5 hover:text-white text-zinc-400 font-medium"
                        >
                            Cancel
                        </Button>
                        <button
                            onClick={handleSubmit}
                            disabled={isSubmitting}
                            className="glass-button-white h-10 px-4 text-sm font-medium text-black disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />}
                            Send Report
                        </button>
                    </DialogFooter>
                </div>
            </DialogContent>
        </Dialog>
    );
}
