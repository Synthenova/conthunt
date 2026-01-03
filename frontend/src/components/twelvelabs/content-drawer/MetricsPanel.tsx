interface MetricsPanelProps {
    item: any;
}

export function MetricsPanel({ item }: MetricsPanelProps) {
    const views = Number(item.view_count || item.views || 0);
    const likes = Number(item.like_count || item.likes || 0);
    const comments = Number(item.comment_count || item.comments || 0);
    const shares = Number(item.share_count || item.shares || 0);

    const engagement = views === 0 ? "0%" : `${(((likes + comments + shares) / views) * 100).toFixed(2)}%`;

    return (
        <div className="grid grid-cols-4 gap-4 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
            <Metric label="Views" value={formatMetric(views)} />
            <Metric label="Likes" value={formatMetric(likes)} />
            <Metric label="Comments" value={formatMetric(comments)} />
            <Metric label="Eng." value={engagement} />
        </div>
    );
}

function Metric({ label, value }: { label: string; value: string }) {
    return (
        <div className="text-center">
            <div className="text-lg font-bold text-white mb-1">{value}</div>
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">{label}</div>
        </div>
    );
}

function formatMetric(num: number): string {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + "M";
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
}
