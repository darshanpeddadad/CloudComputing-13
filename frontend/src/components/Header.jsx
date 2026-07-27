import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";
import { Link, useNavigate, useLocation } from "react-router";
import { useSelector, useDispatch } from "react-redux";
import { logout } from "../store/slices/authSlice";
import { Menu, X, Bell, ArrowUpRight } from "lucide-react";
import { Logo } from "./Logo";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import socketService from "../services/socketService";
import { toast } from "sonner";
import { ThemeToggle } from "./ThemeToggle";

export const Header = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useSelector((s) => s.auth || {});
  const currentPath = useLocation().pathname;

  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [popoverOpen, setPopoverOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleLogout = () => {
    dispatch(logout());
    navigate("/login");
  };

  const actualUser = user?.user || user;
  const avatarSrc =
    actualUser?.avatar || actualUser?.avatar_url || actualUser?.image || null;
  const userRole = actualUser?.roles?.[0];
  const isAdmin = userRole === "admin";

  useEffect(() => {
    if (!isAdmin) return;

    // manual join to the admin_global room as auto join did not work
    socketService.joinAdminRoom();

    // listen for SOS alerts
    const unsubSOS = socketService.onSOSAlert((data) => {
      setNotifications((prev) => [data, ...prev]);
    });

    return () => unsubSOS();
  }, [isAdmin]);

  const navLinks = isAuthenticated
    ? [
      { label: "Events", path: "/events" },
      { label: "Resale Market", path: "/resale-market" },
    ]
    : [
      { label: "Home", path: "/" },
      { label: "Events", path: "/events" },
      { label: "About", path: "/about" },
    ];

  return (
    <nav className="fixed top-[52px] left-0 right-0 z-50 transition-all duration-500 flex justify-center px-4">
      <div
        className={`flex items-center justify-between px-2 py-2 pr-8 md:pr-2 md:pl-8 rounded-full border border-white/60 dark:border-white/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.3)] backdrop-blur-xl transition-all duration-500 ${scrolled
          ? "bg-white/80 dark:bg-card/80 w-full max-w-4xl shadow-sky-100/50 dark:shadow-sky-900/30"
          : "bg-white/50 dark:bg-card/50 w-full max-w-6xl"
          }`}
      >
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <Link to="/events" className="flex items-center gap-3">
              <Logo className="text-xl md:text-2xl" />
            </Link>
          ) : (
            <Link to="/" className="flex items-center gap-3">
              <Logo className="text-xl md:text-2xl" />
            </Link>
          )}
        </div>

        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((item) => {
            const isActive =
              item.path === "/"
                ? currentPath === "/"
                : currentPath.startsWith(item.path);

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative px-5 py-2.5 rounded-full text-sm font-medium transition-all duration-300 group ${isActive
                  ? "text-white bg-gradient-to-r from-primary to-secondary shadow-sm shadow-primary/30"
                  : "text-muted-foreground hover:text-primary hover:bg-primary/5"
                  }`}
              >
                <span className="relative z-10">{item.label}</span>
                {!isActive && (
                  <span className="absolute inset-0 rounded-full bg-gradient-to-r from-primary/10 to-secondary/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
                )}
              </Link>
            );
          })}
        </div>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <div className="hidden md:flex items-center gap-3">
              <Link to="/events/create">
                <Button variant="outline" size="sm" className="rounded-full">
                  Create Event
                </Button>
              </Link>

              {isAdmin && (
                <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="relative rounded-full"
                    >
                      <Bell
                        className={`w-5 h-5 ${notifications.length > 0
                          ? "text-red-500 animate-pulse"
                          : "text-muted-foreground"
                          }`}
                      />
                      {notifications.length > 0 && (
                        <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white animate-bounce" />
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-80 p-0" align="end">
                    <div className="p-4 border-b bg-destructive/5">
                      <h4 className="font-semibold text-sm text-destructive flex items-center gap-2">
                        Emergency Alerts
                      </h4>
                    </div>
                    <div className="max-h-[300px] overflow-y-auto">
                      {notifications.length === 0 ? (
                        <div className="p-8 text-center text-sm text-muted-foreground">
                          No active emergencies.
                        </div>
                      ) : (
                        notifications.map((notif, i) => (
                          <div
                            key={i}
                            className="group p-3 border-b last:border-0 hover:bg-muted/50 transition-colors cursor-pointer relative"
                            onClick={() => {
                              setNotifications((prev) => prev.filter((_, idx) => idx !== i));
                              setPopoverOpen(false);
                              navigate("/admin/dashboard?tab=sos");
                            }}
                          >
                            <div className="flex items-start gap-3">
                              <div className="w-2 h-2 mt-2 rounded-full bg-red-500 shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
                              <div className="flex-1 space-y-1">
                                <div className="flex justify-between items-start">
                                  <p className="text-sm font-semibold text-red-600">
                                    {notif.event_title || "Unknown Event"}
                                  </p>
                                  <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-all group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                                </div>
                                <p className="text-sm text-foreground font-medium">
                                  {notif.user_name}
                                </p>
                                <p className="text-xs text-muted-foreground italic">
                                  "{notif.message}"
                                </p>
                                <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/50">
                                  <span className="text-[10px] text-muted-foreground">
                                    {new Date(
                                      notif.created_at
                                    ).toLocaleTimeString()}
                                  </span>
                                  {notif.latitude && notif.longitude && (
                                    <a
                                      href={`https://www.google.com/maps?q=${notif.latitude},${notif.longitude}`}
                                      target="_blank"
                                      rel="noreferrer"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                      }}
                                      className="z-10 text-xs text-primary hover:underline font-medium flex items-center gap-1 bg-primary/5 px-2 py-0.5 rounded-full hover:bg-primary/10 transition-colors"
                                    >
                                      Open Map
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </PopoverContent>
                </Popover>
              )}

              <Link
                to={
                  userRole === "admin" ? "/admin/dashboard" : "/user/dashboard"
                }
              >
                <Avatar className="w-9 h-9 border-2 border-primary/20 hover:border-primary/50 transition-colors cursor-pointer">
                  {avatarSrc ? (
                    <AvatarImage
                      src={avatarSrc}
                      alt={actualUser?.name || actualUser?.email}
                    />
                  ) : (
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {actualUser?.name?.[0]?.toUpperCase() ||
                        actualUser?.email?.[0]?.toUpperCase() ||
                        "U"}
                    </AvatarFallback>
                  )}
                </Avatar>
              </Link>
            </div>
          ) : (
            currentPath !== "/login" &&
            currentPath !== "/register" && (
              <div className="hidden md:flex items-center gap-2">
                <Link to="/login">
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-full hover:bg-primary/5 hover:text-primary hover:border-primary/50 transition-all duration-300"
                  >
                    Login
                  </Button>
                </Link>
                <Link to="/register">
                  <Button
                    size="sm"
                    className="rounded-full shadow-lg shadow-primary/30 hover:shadow-xl hover:shadow-primary/40 hover:scale-105 transition-all duration-300"
                  >
                    Register
                  </Button>
                </Link>
              </div>
            )
          )}

          <button
            className="md:hidden p-2 rounded-full bg-accent hover:bg-accent/80 text-foreground transition-colors"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
          <ThemeToggle />

        </div>
      </div>

      {/* Dropdown for small screen */}
      {mobileOpen && (
        <div className="md:hidden absolute top-full left-4 right-4 mt-2 bg-white/95 dark:bg-card/95 backdrop-blur-xl rounded-3xl border border-white/60 dark:border-white/10 shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 animate-fadeIn">
          <div className="flex flex-col gap-2">
            {navLinks.map((item) => {
              const isActive =
                item.path === "/"
                  ? currentPath === "/"
                  : currentPath.startsWith(item.path);

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`px-5 py-3 rounded-2xl text-base font-medium transition-all ${isActive
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                    }`}
                >
                  {item.label}
                </Link>
              );
            })}

            <div className="border-t border-border my-3"></div>

            {isAuthenticated ? (
              <>
                <Link to="/events/create" onClick={() => setMobileOpen(false)}>
                  <Button variant="outline" className="w-full rounded-2xl">
                    Create Event
                  </Button>
                </Link>
                <Link
                  to={
                    userRole === "admin"
                      ? "/admin/dashboard"
                      : "/user/dashboard"
                  }
                  onClick={() => setMobileOpen(false)}
                >
                  <Button variant="ghost" className="w-full rounded-2xl">
                    Dashboard
                  </Button>
                </Link>
                <Button
                  variant="destructive"
                  className="w-full rounded-2xl"
                  onClick={() => {
                    handleLogout();
                    setMobileOpen(false);
                  }}
                >
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Link to="/login" onClick={() => setMobileOpen(false)}>
                  <Button
                    variant="outline"
                    className="w-full rounded-2xl hover:bg-primary/5 hover:text-primary hover:border-primary/50 transition-all duration-300"
                  >
                    Login
                  </Button>
                </Link>
                <Link to="/register" onClick={() => setMobileOpen(false)}>
                  <Button className="w-full rounded-2xl shadow-lg shadow-primary/30 hover:shadow-xl hover:scale-105 transition-all duration-300">
                    Register
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};
