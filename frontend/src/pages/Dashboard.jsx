import Myevents from "@/components/userDashboardTabs/Myevents";
import Mytickets from "@/components/userDashboardTabs/Mytickets";
import Resale from "@/components/userDashboardTabs/Resale";
import Rewards from "@/components/userDashboardTabs/Rewards";
import Profile from "@/components/userDashboardTabs/Profile";
import Bookmarks from "@/components/userDashboardTabs/Bookmarks";
import EventEditRequests from "@/components/userDashboardTabs/EventEditRequests";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useDispatch } from "react-redux";
import { logout } from "@/store/slices/authSlice";
import { LogOut } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Dashboard() {
  const dispatch = useDispatch();
  const [activeTab, setActiveTab] = useState("profile");

  const handleLogout = () => {
    dispatch(logout());
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
                User Dashboard
              </h1>
              <p className="text-muted-foreground">
                Manage your profile, tickets, and events
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
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2 md:grid-cols-7 mb-8 h-auto gap-2 bg-transparent p-0">
                <TabsTrigger
                  className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                  value="profile"
                >
                  Profile
                </TabsTrigger>
                <TabsTrigger
                  className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                  value="mytickets"
                >
                  My Tickets
                </TabsTrigger>
                <TabsTrigger
                  className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                  value="myevents"
                >
                  My Events
                </TabsTrigger>
                <TabsTrigger
                  className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                  value="bookmarks"
                >
                  Bookmarks
                </TabsTrigger>
                <TabsTrigger
                  className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                  value="editrequests"
                >
                  Edit Requests
                </TabsTrigger>
                <TabsTrigger
                  className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                  value="resale"
                >
                  Resale
                </TabsTrigger>
                <TabsTrigger
                  className="cursor-pointer data-[state=active]:bg-primary/10 data-[state=active]:text-primary data-[state=active]:shadow-none border border-transparent data-[state=active]:border-primary/20 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-200 py-3 rounded-xl"
                  value="rewards"
                >
                  Rewards
                </TabsTrigger>
              </TabsList>

              <div className="mt-6 bg-white/50 dark:bg-card/50 rounded-xl p-6 border border-primary/5 min-h-[500px]">
                <TabsContent
                  value="profile"
                  className="mt-0 focus-visible:ring-0"
                >
                  <Profile />
                </TabsContent>
                <TabsContent
                  value="mytickets"
                  className="mt-0 focus-visible:ring-0"
                >
                  <Mytickets />
                </TabsContent>
                <TabsContent
                  value="bookmarks"
                  className="mt-0 focus-visible:ring-0"
                >
                  <Bookmarks />
                </TabsContent>
                <TabsContent
                  value="myevents"
                  className="mt-0 focus-visible:ring-0"
                >
                  <Myevents />
                </TabsContent>
                <TabsContent
                  value="editrequests"
                  className="mt-0 focus-visible:ring-0"
                >
                  <EventEditRequests />
                </TabsContent>
                <TabsContent
                  value="resale"
                  className="mt-0 focus-visible:ring-0"
                >
                  <Resale />
                </TabsContent>
                <TabsContent
                  value="rewards"
                  className="mt-0 focus-visible:ring-0"
                >
                  <Rewards isActive={activeTab === "rewards"} />
                </TabsContent>
              </div>
            </Tabs>
          </div>
        </div>
      </main>
    </div>
  );
}
