import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";
import { auth } from '@/lib/firebaseClient';
import type { ChatChip, SummaryItem } from './types';

export function normalizeText(value?: string) {
    return value ? value.replace(/\s+/g, ' ').trim() : '';
}

export function truncateText(value: string, limit: number) {
    if (value.length <= limit) return value;
    return value.slice(0, limit - 1).trimEnd() + '…';
}

export function formatChipFence(chip: ChatChip) {
    if (chip.type === 'media') {
        // Format: media | id | platform | title
        return `media | ${chip.media_asset_id} | ${chip.platform} | ${chip.title}`;
    }
    if (chip.type === 'image') {
        // Format: image | id | label
        return `image | ${chip.id} | ${chip.fileName}`;
    }

    // Format: type | id | label
    return `${chip.type} | ${chip.id} | ${chip.label}`;
}

export function formatItemLine(item: SummaryItem) {
    return JSON.stringify({
        title: normalizeText(item.title),
        platform: normalizeText(item.platform),
        creator_handle: normalizeText(item.creator_handle),
        content_type: normalizeText(item.content_type),
        primary_text: normalizeText(item.primary_text),
        media_asset_id: item.media_asset_id || '',
    });
}

export function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes('tiktok')) return FaTiktok;
    if (normalized.includes('instagram')) return FaInstagram;
    if (normalized.includes('youtube')) return FaYoutube;
    if (normalized.includes('pinterest')) return FaPinterest;
    return FaGlobe;
}

export async function fetchWithAuth<T>(url: string, options: RequestInit = {}): Promise<T> {
    const user = auth.currentUser;
    if (!user) throw new Error('User not authenticated');

    const token = await user.getIdToken();
    const res = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API request failed');
    }
    return res.json();
}
