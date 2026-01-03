import { cn } from "@/lib/utils";

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
    hoverEffect?: boolean;
    blur?: "sm" | "md" | "lg" | "xl" | "2xl" | "3xl";
    intensity?: "low" | "medium" | "high";
}

export function GlassPanel({
    children,
    className,
    hoverEffect = false,
    blur = "md",
    intensity = "medium",
    ...props
}: GlassPanelProps) {
    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!hoverEffect) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        e.currentTarget.style.setProperty("--mouse-x", `${x}px`);
        e.currentTarget.style.setProperty("--mouse-y", `${y}px`);
    };

    return (
        <div
            onMouseMove={handleMouseMove}
            className={cn(
                "rounded-xl border border-white/10 transition-all duration-300",
                "glass", // Always apply base glass effect

                // Blur levels overrides (base glass has backdrop-blur-xl)
                blur === "sm" && "backdrop-blur-sm",
                blur === "md" && "backdrop-blur-md",
                blur === "lg" && "backdrop-blur-lg",
                blur === "xl" && "backdrop-blur-xl",
                blur === "2xl" && "backdrop-blur-2xl",
                blur === "3xl" && "backdrop-blur-3xl",
                (blur === "2xl" || blur === "3xl") && "backdrop-saturate-150 backdrop-brightness-110",

                // Background intensity
                intensity === "low" && "bg-white/3",
                intensity === "medium" && "bg-white/5",
                intensity === "high" && "bg-white/10",

                // Hover effects
                hoverEffect && "hover:bg-white/10 hover:border-white/20 hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-0.5 light-torch",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}

/** @deprecated Use GlassPanel instead */
export const GlassCard = GlassPanel;
