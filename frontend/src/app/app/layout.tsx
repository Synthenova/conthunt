import { ChatSidebarGate } from "@/components/chat";
import { Toaster } from "@/components/ui/sonner";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { NavigationReset } from "@/components/layout/NavigationReset";

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen w-full overflow-hidden bg-[#000000]">
            <NavigationReset />
            {/* Left Sidebar */}
            <AppSidebar />

            {/* Main content area */}
            <main className="flex-1 min-w-0 overflow-auto scrollbar-none transition-all duration-300 relative">
                <Toaster />
                {children}
            </main>

            {/* Right Chat Sidebar + Toggle (hidden on /app) */}
            <ChatSidebarGate />
        </div>
    );
}
