import Image from "next/image";

interface ChatEmptyStateProps {
    state: "loading" | "empty";
}

export function ChatEmptyState({ state }: ChatEmptyStateProps) {
    const message = "Loading your canvas, hang tight!";

    return (
        <div className="min-h-[70vh] flex items-center justify-center">
            <div className="flex flex-col items-center gap-4 text-center">
                {/* Logo with spinner ring */}
                <div className="relative">
                    {/* Spinner ring */}
                    <div
                        className="absolute rounded-full border-2 border-transparent border-t-white animate-spin"
                        style={{
                            width: '72px',
                            height: '72px',
                            top: '-4px',
                            left: '-4px',
                        }}
                    />
                    {/* Logo */}
                    <div className="h-16 w-16 rounded-full overflow-hidden bg-white/5 flex items-center justify-center">
                        <Image
                            src="/images/image.png"
                            alt="Logo"
                            width={54}
                            height={54}
                            priority
                            className="object-contain"
                        />
                    </div>
                </div>

                {/* Message */}
                <p className="text-sm text-muted-foreground max-w-xs">
                    {message}
                </p>
            </div>
        </div>
    );
}
