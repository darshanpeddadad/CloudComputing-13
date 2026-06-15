import { useEffect } from "react";
import { Outlet, useLocation } from "react-router";
import { Header } from "./Header";
import { Disclaimer } from "./Disclaimer";
import ChatWidget from "./chat/ChatWidget";
import { useSelector } from "react-redux";
import socketService from "../services/socketService";

const Layout = () => {
  const { isAuthenticated, user } = useSelector((state) => state.auth || {});
  const location = useLocation();

  const hideHeader =
    location.pathname === "/login" || location.pathname === "/register";

  // global socket service connect
  useEffect(() => {
    const token = user?.access_token;
    if (isAuthenticated && token) {
      socketService.connect(token);
    } else {
      socketService.disconnect();
    }
  }, [isAuthenticated, user?.access_token]);

  return (
    <div className="min-h-screen bg-background">
      <Disclaimer />
      {!hideHeader && <Header />}
      <div className={hideHeader ? "" : "pt-22"}>
        <Outlet />
      </div>
      {isAuthenticated && <ChatWidget />}
    </div>
  );
};

export default Layout;
