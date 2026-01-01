
import { useEffect } from 'react';
import { useSearchStream } from '@/hooks/useSearchStream';
import { transformSearchResults, FlatMediaItem } from '@/lib/transformers';

interface SearchStreamerProps {
    searchId: string;
    onResults: (searchId: string, results: FlatMediaItem[]) => void;
    onStreamingChange?: (searchId: string, isStreaming: boolean) => void;
    onLoadingChange?: (searchId: string, isLoading: boolean) => void;
}

export function SearchStreamer({ searchId, onResults, onStreamingChange, onLoadingChange }: SearchStreamerProps) {
    const { results, isStreaming, isLoading } = useSearchStream(searchId);

    useEffect(() => {
        // Transform the raw results to FlatMediaItem
        const transformed = transformSearchResults(results || []);
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

    return null;
}
