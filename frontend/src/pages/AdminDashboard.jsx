
import { Button } from "@/components/ui/button";
import { useDispatch } from "react-redux";
import { logout } from "@/store/slices/authSlice";
import { LogOut } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import EventApproval from "@/components/adminDashboardTabs/EventApproval";
import EventModification from "@/components/adminDashboardTabs/EventModification";
import UserManagement from "@/components/adminDashboardTabs/UserManagement";
// import ContentModeration from "@/components/adminDashboardTabs/ContentModeration";
import SOS from "@/components/adminDashboardTabs/SOS";
import { useSearchParams } from "react-router";


const AdminDashboard = () => {

    const dispatch = useDispatch();
    const [searchParams, setSearchParams] = useSearchParams();
    const activeTab = searchParams.get("tab") || "eventapproval";

    const handleLogout = () => {
        dispatch(logout());
    };

    const handleTabChange = (value) => {
        setSearchParams({ tab: value });
    };

    return (
        <div className="min-h-screen bg-background">
            {/* Background Gradients */}
            <div className="fixed inset-0 bg-linear-to-br from-blue-50 via-white to-sky-50 dark:from-blue-950/30 dark:via-background dark:to-sky-950/30 -z-10" />
            <div className="fixed inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(59,130,246,0.15),transparent_50%),radial-gradient(circle_at_70%_80%,rgba(14,165,233,0.12),transparent_50%)] -z-10" />

            <main className="container mx-auto px-4 py-8 md:py-12 relative">
                <div className="max-w-8xl mx-auto space-y-8">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-white/60 dark:bg-card/60 backdrop-blur-sm border border-primary/10 p-6 rounded-2xl shadow-sm">
                        <div className="space-y-1">
                            <h1 className="text-3xl md:text-4xl font-bold bg-linear-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                                Admin Dashboard
                            </h1>
                            <p className="text-muted-foreground">
                                Manage events, users, and content
                            </p>
                        </div>
                        <Button
                            className="shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 bg-white/80 dark:bg-card/80 backdrop-blur-sm hover:bg-destructive/10 hover:text-destructive hover:border-destructive/50 border border-transparent"
                            variant="outline"
                            onClick={handleLogout}
                        >
                            <LogOut className="mr-2 h-4 w-4" />
                            Log out
                        </Button>
                    </div>

                    <div className="bg-white/40 dark:bg-card/40 backdrop-blur-sm border border-white/20 dark:border-white/10 rounded-2xl p-6 shadow-xl">
                        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
                            <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 mb-8 h-auto gap-2 bg-transparent p-0">
                                <TabsTrigger
                                    className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                                    value="eventapproval"
                                >
                                    Event Approval
                                </TabsTrigger>
                                <TabsTrigger
                                    className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                                    value="eventmodification"
                                >
                                    Event Modification
                                </TabsTrigger>
                                <TabsTrigger
                                    className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                                    value="usermanagement"
                                >
                                    User Management
                                </TabsTrigger>
                                {/* <TabsTrigger
                                    className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                                    value="contentmoderation"
                                >
                                    Content Moderation
                                </TabsTrigger> */}
                                <TabsTrigger
                                    className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                                    value="sos"
                                >
                                    SOS
                                </TabsTrigger>
                            </TabsList>

                            <div className="mt-6 bg-white/50 dark:bg-card/50 rounded-xl p-6 border border-primary/5 min-h-[500px]">
                                <TabsContent value="eventapproval" className="mt-0 focus-visible:ring-0">
                                    <EventApproval />
                                </TabsContent>
                                <TabsContent value="eventmodification" className="mt-0 focus-visible:ring-0">
                                    <EventModification />
                                </TabsContent>
                                <TabsContent value="usermanagement" className="mt-0 focus-visible:ring-0">
                                    <UserManagement />
                                </TabsContent>
                                {/* <TabsContent value="contentmoderation" className="mt-0 focus-visible:ring-0">
                                    <ContentModeration />
                                </TabsContent> */}
                                <TabsContent value="sos" className="mt-0 focus-visible:ring-0">
                                    <SOS />
                                </TabsContent>
                            </div>
                        </Tabs>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default AdminDashboard