import * as React from "react"
import { Search } from "lucide-react"
import { cn } from "@/lib/utils"

export interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> { }

const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
    ({ className, ...props }, ref) => {
        return (
            <div className={cn("relative group w-full", className)}>
                <div className="absolute inset-0 bg-primary/5 rounded-xl blur-md group-hover:bg-primary/10 transition-colors pointer-events-none" />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors pointer-events-none">
                    <Search className="h-4 w-4" />
                </div>
                <input
                    ref={ref}
                    type="text"
                    className="relative w-full glass bg-surface/50 border border-white/10 text-white placeholder-gray-500 text-sm rounded-xl pl-10 pr-4 py-2.5 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
                    {...props}
                />
            </div>
        )
    }
)
SearchInput.displayName = "SearchInput"

export { SearchInput }
