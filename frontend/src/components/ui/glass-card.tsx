import { cn } from "@/lib/utils";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
    hoverEffect?: boolean;
    blur?: "sm" | "md" | "lg" | "xl";
    intensity?: "low" | "medium" | "high";
}

export function GlassCard({
    children,
    className,
    hoverEffect = false,
    blur = "md",
    intensity = "medium",
    ...props
}: GlassCardProps) {
    return (
        <div
            className={cn(
                "rounded-xl border border-white/10 transition-all duration-300",
                // Blur levels
                blur === "sm" && "backdrop-blur-sm",
                blur === "md" && "backdrop-blur-md",
                blur === "lg" && "backdrop-blur-lg",
                blur === "xl" && "backdrop-blur-xl",

                // Background intensity
                intensity === "low" && "bg-white/5",
                intensity === "medium" && "bg-white/10",
                intensity === "high" && "bg-white/15",

                // Hover effects
                hoverEffect && "hover:bg-white/15 hover:border-white/20 hover:shadow-lg hover:-translate-y-1",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}
