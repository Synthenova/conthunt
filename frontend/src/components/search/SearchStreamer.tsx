
import { useEffect } from 'react';
import { useSearchStream } from '@/hooks/useSearchStream';
import { transformSearchResults, FlatMediaItem } from '@/lib/transformers';

interface SearchStreamerProps {
    searchId: string;
    onResults: (searchId: string, results: FlatMediaItem[]) => void;
}

export function SearchStreamer({ searchId, onResults }: SearchStreamerProps) {
    const { results } = useSearchStream(searchId);

    useEffect(() => {
        // Transform the raw results to FlatMediaItem
        const transformed = transformSearchResults(results || []);
        onResults(searchId, transformed);
    }, [results, searchId, onResults]);

    return null;
}
