"use client";

import React, { useMemo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Gift, Mail, MessageSquare, Link as LinkIcon } from "lucide-react";
import {
  FaXTwitter,
  FaWhatsapp,
  FaTelegram,
  FaFacebookF,
  FaLinkedinIn,
  FaPinterestP,
  FaRedditAlien,
} from "react-icons/fa6";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface GiftShareModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SHARE_URL = "https://conthunt.app";
const SHARE_TEXT = 'try out "https://conthunt.app"';
const SHARE_TITLE = "Conthunt";
const PINTEREST_IMAGE = `${SHARE_URL}/images/logo-title-white.png`;

function enc(value?: string) {
  return encodeURIComponent(value || "");
}

function shareLinks({
  url,
  text,
  title,
}: {
  url: string;
  text?: string;
  title?: string;
}) {
  const U = enc(url);
  const T = enc(text || title || "");

  return {
    x: `https://twitter.com/intent/tweet?text=${T}&url=${U}`,
    whatsapp: `https://wa.me/?text=${enc((text ? `${text} ` : "") + url)}`,
    telegram: `https://t.me/share/url?url=${U}&text=${T}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${U}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${U}`,
    email: `mailto:?subject=${enc(title || "Check this out")}&body=${enc(
      (text ? `${text}\n\n` : "") + url
    )}`,
    sms: `sms:?body=${enc((text ? `${text} ` : "") + url)}`,
    pinterest: (imageUrl: string) =>
      `https://www.pinterest.com/pin/create/button/?url=${U}&media=${enc(
        imageUrl
      )}&description=${T}`,
    reddit: `https://www.reddit.com/submit?url=${U}&title=${enc(title || "")}`,
  };
}

export function GiftShareModal({ isOpen, onClose }: GiftShareModalProps) {
  const [isCopying, setIsCopying] = useState(false);

  const links = useMemo(
    () =>
      shareLinks({
        url: SHARE_URL,
        text: SHARE_TEXT,
        title: SHARE_TITLE,
      }),
    []
  );

  const handleCopy = async () => {
    if (!navigator?.clipboard) {
      toast.error("Clipboard not available.");
      return;
    }
    try {
      setIsCopying(true);
      await navigator.clipboard.writeText(SHARE_URL);
      toast.success("Link copied!");
    } catch (error) {
      console.error(error);
      toast.error("Couldn't copy link.");
    } finally {
      setIsCopying(false);
    }
  };

  const shareItems = [
    { key: "x", label: "X", href: links.x, icon: FaXTwitter },
    { key: "whatsapp", label: "WhatsApp", href: links.whatsapp, icon: FaWhatsapp },
    { key: "telegram", label: "Telegram", href: links.telegram, icon: FaTelegram },
    { key: "facebook", label: "Facebook", href: links.facebook, icon: FaFacebookF },
    { key: "linkedin", label: "LinkedIn", href: links.linkedin, icon: FaLinkedinIn },
    { key: "reddit", label: "Reddit", href: links.reddit, icon: FaRedditAlien },
    {
      key: "pinterest",
      label: "Pinterest",
      href: links.pinterest(PINTEREST_IMAGE),
      icon: FaPinterestP,
    },
    { key: "email", label: "Email", href: links.email, icon: Mail },
    { key: "sms", label: "SMS", href: links.sms, icon: MessageSquare },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[560px] bg-[#0A0A0A] border-[#1F1F1F] text-gray-100">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Gift className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <DialogTitle>Share & Gift</DialogTitle>
              <DialogDescription className="text-gray-400">
                Help us grow by sharing Conthunt with your community.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <LinkIcon className="h-3.5 w-3.5" />
              <span>Message</span>
            </div>
            <p className="mt-2 text-sm text-gray-200">{SHARE_TEXT}</p>
            <p className="mt-1 text-xs text-gray-500">{SHARE_URL}</p>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {shareItems.map((item) => {
              const Icon = item.icon as React.ElementType;
              return (
                <a
                  key={item.key}
                  href={item.href}
                  target="_blank"
                  rel="noreferrer"
                  className={cn(
                    "flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-gray-200 transition-all",
                    "hover:border-white/20 hover:bg-white/[0.06]"
                  )}
                >
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/[0.06] text-gray-200">
                    <Icon className="h-4 w-4" />
                  </span>
                  <span className="truncate">{item.label}</span>
                </a>
              );
            })}
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="ghost"
            onClick={onClose}
            className="hover:bg-white/5 hover:text-white"
          >
            Close
          </Button>
          <Button
            onClick={handleCopy}
            disabled={isCopying}
            className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2"
          >
            <LinkIcon className="h-4 w-4" />
            Copy link
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
