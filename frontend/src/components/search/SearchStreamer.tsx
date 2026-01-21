
import { useEffect } from 'react';
import { useSearchStream } from '@/hooks/useSearchStream';
import { transformSearchResults, FlatMediaItem } from '@/lib/transformers';

interface SearchStreamerProps {
    searchId: string;
    onResults: (searchId: string, results: FlatMediaItem[]) => void;
    onStreamingChange?: (searchId: string, isStreaming: boolean) => void;
    onLoadingChange?: (searchId: string, isLoading: boolean) => void;
    onCursorsChange?: (searchId: string, cursors: Record<string, any>, hasMore: boolean) => void;
}

export function SearchStreamer({
    searchId,
    onResults,
    onStreamingChange,
    onLoadingChange,
    onCursorsChange
}: SearchStreamerProps) {
    const { results, cursors, hasMore, isStreaming, isLoading } = useSearchStream(searchId);

    useEffect(() => {
        // Transform the raw results to FlatMediaItem
        const transformed = transformSearchResults(results || []);
        console.log('[SearchStreamer] Sending results for searchId:', searchId, 'count:', transformed.length);
        onResults(searchId, transformed);
    }, [results, searchId, onResults]);

    useEffect(() => {
        if (!onStreamingChange) return;
        onStreamingChange(searchId, isStreaming);
    }, [isStreaming, searchId, onStreamingChange]);

    useEffect(() => {
        if (!onLoadingChange) return;
        onLoadingChange(searchId, isLoading);
    }, [isLoading, searchId, onLoadingChange]);

    useEffect(() => {
        if (!onCursorsChange) return;
        onCursorsChange(searchId, cursors, hasMore);
    }, [cursors, hasMore, searchId, onCursorsChange]);

    return null;
}
