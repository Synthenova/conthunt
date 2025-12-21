"use client";

import { Search, History, LayoutDashboard, Settings, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarRail,
    SidebarTrigger,
} from "@/components/ui/sidebar";
import { LogoutButton } from "@/components/logout-button";

const navItems = [
    {
        title: "Search",
        url: "/app",
        icon: Search,
    },
    {
        title: "History",
        url: "/app/history",
        icon: History,
    },
    {
        title: "Boards",
        url: "/app/boards",
        icon: LayoutDashboard,
    },
];

export function AppSidebar() {
    const pathname = usePathname();

    return (
        <Sidebar collapsible="icon" className="border-r border-white/5">
            <SidebarHeader className="p-4 group-data-[collapsible=icon]:p-2 transition-all">
                <div className="flex items-center justify-between px-2 group-data-[collapsible=icon]:px-0">
                    <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shrink-0">
                            <span className="font-bold text-lg">C</span>
                        </div>
                        <span className="font-semibold text-lg group-data-[collapsible=icon]:hidden">Conthunt</span>
                    </div>
                    <SidebarTrigger className="group-data-[collapsible=icon]:hidden ml-auto h-8 w-8" />
                </div>
                <div className="hidden group-data-[collapsible=icon]:flex items-center justify-center py-2">
                    <SidebarTrigger className="h-8 w-8" />
                </div>
            </SidebarHeader>
            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupLabel className="group-data-[collapsible=icon]:hidden">Navigation</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {navItems.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton
                                        asChild
                                        isActive={pathname === item.url}
                                        tooltip={item.title}
                                    >
                                        <Link href={item.url}>
                                            <item.icon className="h-4 w-4" />
                                            <span>{item.title}</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
            <SidebarFooter>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <LogoutButton className="w-full flex justify-start items-center gap-2 p-2 px-3 text-sm hover:bg-sidebar-accent hover:text-sidebar-accent-foreground rounded-md transition-colors" />
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarFooter>
            <SidebarRail />
        </Sidebar>
    );
}
