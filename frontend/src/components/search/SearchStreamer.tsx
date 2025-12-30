
import { useEffect } from 'react';
import { useSearchStream } from '@/hooks/useSearchStream';
import { transformSearchResults, FlatMediaItem } from '@/lib/transformers';

interface SearchStreamerProps {
    searchId: string;
    onResults: (searchId: string, results: FlatMediaItem[]) => void;
    onStreamingChange?: (searchId: string, isStreaming: boolean) => void;
}

export function SearchStreamer({ searchId, onResults, onStreamingChange }: SearchStreamerProps) {
    const { results, isStreaming } = useSearchStream(searchId);

    useEffect(() => {
        // Transform the raw results to FlatMediaItem
        const transformed = transformSearchResults(results || []);
        onResults(searchId, transformed);
    }, [results, searchId, onResults]);

    useEffect(() => {
        if (!onStreamingChange) return;
        onStreamingChange(searchId, isStreaming);
    }, [isStreaming, searchId, onStreamingChange]);

    return null;
}
