import { ChatSidebar, ChatToggleButton } from "@/components/chat";
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
        <SidebarProvider style={{ "--sidebar-width": "320px" } as Record<string, string>}>
            <NavigationReset />
            <div className="flex h-screen w-full overflow-hidden">
                <SidebarTrigger className="md:hidden absolute top-4 left-4 z-50 text-white" />
                {/* Left Sidebar */}
                <AppSidebar />

                {/* Main content area */}
                <main className="flex-1 min-w-0 overflow-auto scrollbar-none transition-all duration-300 relative">
                    {children}
                </main>

                {/* Right Chat Sidebar */}
                <ChatSidebar />

                {/* Floating toggle button */}
                <ChatToggleButton />

                {/* Toast notifications */}
                <Toaster />
            </div>
        </SidebarProvider>
    );
}
