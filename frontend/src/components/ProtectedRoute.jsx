import { Navigate } from "react-router";
import { useSelector } from "react-redux";

export default function ProtectedRoute({ children, requiredRole }) {
  const { isAuthenticated, user } = useSelector((state) => state.auth);

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check for role-based access if requiredRole is specified
  if (requiredRole && user) {
    // Handle nested user object structure
    const userRoles = user.user?.roles || user.roles;
    const userRole = userRoles?.[0];

    if (requiredRole === "admin" && userRole !== "admin") {
      return <Navigate to="/user/dashboard" replace />;
    }

    if (requiredRole === "user" && userRole === "admin") {
      return <Navigate to="/admin/dashboard" replace />;
    }
  }

  // Render protected content if authenticated and authorized
  return children;
}

