
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function ChatLoader() {
    return (
        <div className="flex flex-col gap-4 p-4 w-full">
            {/* AI Message Skeleton (Left) */}
            <div className="flex w-full justify-start">
                <div className="flex flex-col gap-2 max-w-[85%]">
                    <Skeleton className="h-4 w-[250px]" />
                    <Skeleton className="h-4 w-[200px]" />
                </div>
            </div>

            {/* User Message Skeleton (Right) */}
            <div className="flex w-full justify-end">
                <div className="flex flex-col gap-2 items-end max-w-[85%]">
                    <Skeleton className="h-10 w-[300px] rounded-xl" />
                </div>
            </div>

            {/* AI Message Skeleton (Left) */}
            <div className="flex w-full justify-start">
                <div className="flex flex-col gap-2 max-w-[85%]">
                    <Skeleton className="h-4 w-[280px]" />
                    <Skeleton className="h-4 w-[180px]" />
                    <Skeleton className="h-4 w-[220px]" />
                </div>
            </div>

            {/* User Message Skeleton (Right) */}
            <div className="flex w-full justify-end">
                <div className="flex flex-col gap-2 items-end max-w-[85%]">
                    <Skeleton className="h-10 w-[150px] rounded-xl" />
                </div>
            </div>

            {/* AI Message Skeleton (Left) */}
            <div className="flex w-full justify-start">
                <div className="flex flex-col gap-2 max-w-[85%]">
                    <Skeleton className="h-4 w-[260px]" />
                    <Skeleton className="h-4 w-[240px]" />
                </div>
            </div>
        </div>
    );
}
