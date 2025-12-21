import { ChatSidebar, ChatToggleButton } from "@/components/chat";
import { Toaster } from "@/components/ui/sonner";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/AppSidebar";

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <SidebarProvider>
            <div className="flex h-screen w-full overflow-hidden">
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
