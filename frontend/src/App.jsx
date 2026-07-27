import { useEffect } from "react";
import { Provider, useDispatch, useSelector } from "react-redux";
import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import { store } from "./store/store";
import { setTheme } from "./store/slices/themeSlice";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import AdminDashboard from "./pages/AdminDashboard";
import Events from "./pages/Events";
import EventDetail from "./pages/EventDetail";
import NotFound from "./pages/NotFound";
import { autoLogin, finishAppLoading } from "./store/slices/authSlice";
import { Toaster } from "sonner";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import CreateEvent from "./pages/CreateEvent";
import EditEvent from "./pages/EditEvent";
import HomePage from "./pages/HomePage";
import About from "./pages/About";
import CreateTicketTypes from "./pages/CreateTicketTypes";
import ResaleMarket from "./pages/ResaleMarket";

// executed on first load to set the theme
const ThemeInitializer = () => {
  useEffect(() => {
    const theme = localStorage.getItem("theme");
    if (theme) {
      store.dispatch(setTheme(theme));
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)")
        .matches;
      store.dispatch(setTheme(prefersDark ? "dark" : "light"));
    }
  }, []);

  return null;
};

const AppRouter = () => {
  const dispatch = useDispatch();
  const { isAuthenticated, isAppLoading } = useSelector((state) => state.auth);

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        dispatch(autoLogin(user));
      } catch (error) {
        localStorage.removeItem("user");
        dispatch(finishAppLoading());
      }
    } else {
      dispatch(finishAppLoading());
    }
  }, [dispatch]);

  // Prevent flicker by waiting for initial auth check
  if (isAppLoading) return null;

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route
            path="/user/dashboard"
            element={
              <ProtectedRoute requiredRole="user">
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={isAuthenticated ? <Navigate to="/events" replace /> : <HomePage />}
          />
          <Route path="/events" element={<Events />} />
          <Route path="/events/:id" element={<EventDetail />} />
          <Route path="/events/create" element={<CreateEvent />} />
          <Route
            path="/events/edit/:id"
            element={
              <ProtectedRoute requiredRole="user">
                <EditEvent />
              </ProtectedRoute>
            }
          />
          <Route path="/events/:eventId/ticket-types" element={<CreateTicketTypes />} />
          <Route path="/about" element={<About />} />
          <Route path="/resale-market" element={<ResaleMarket />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

const App = () => (
  <Provider store={store}>
    <ThemeInitializer />
    <Toaster />
    <AppRouter />
  </Provider>
);
export default App;
