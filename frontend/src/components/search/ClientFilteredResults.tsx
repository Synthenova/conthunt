import { useEffect } from "react";
import { ClientResultControls } from "@/components/search/ClientResultControls";
import { SelectableResultsGrid } from "@/components/search/SelectableResultsGrid";
import { useClientResultSort } from "@/hooks/useClientResultSort";
import { FlatMediaItem } from "@/lib/transformers";

interface ClientFilteredResultsProps {
    results: any[];
    loading: boolean;
    analysisDisabled?: boolean;
    resultsAreFlat?: boolean;
    onFlatResultsChange?: (results: FlatMediaItem[]) => void;
    onAllResultsChange?: (results: FlatMediaItem[]) => void;
}

export function ClientFilteredResults({
    results,
    loading,
    analysisDisabled = false,
    resultsAreFlat = false,
    onFlatResultsChange,
    onAllResultsChange,
}: ClientFilteredResultsProps) {
    const {
        baseResults,
        flatResults,
        clientSort,
        setClientSort,
        clientDateFilter,
        setClientDateFilter,
    } = useClientResultSort(results, { resultsAreFlat });

    useEffect(() => {
        onFlatResultsChange?.(flatResults);
    }, [flatResults, onFlatResultsChange]);

    useEffect(() => {
        onAllResultsChange?.(baseResults);
    }, [baseResults, onAllResultsChange]);

    return (
        <div className="space-y-4">
            <ClientResultControls
                sort={clientSort}
                onSortChange={setClientSort}
                dateFilter={clientDateFilter}
                onDateFilterChange={setClientDateFilter}
                totalResults={flatResults.length}
            />
            <SelectableResultsGrid
                results={flatResults}
                loading={loading}
                analysisDisabled={analysisDisabled}
            />
        </div>
    );
}
