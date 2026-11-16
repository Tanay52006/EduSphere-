import { useQuery } from "@tanstack/react-query";
import { Navigate, useLocation } from "react-router-dom";
import { Skeleton } from "./components/ui";
import { api } from "./lib/api";
import { AuthScreen } from "./pages/AuthScreen";
import { Onboarding } from "./pages/Onboarding";
import { Shell } from "./pages/Shell";

export default function App() {
  const me = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false });
  const location = useLocation();
  if (me.isPending)
    return (
      <div className="loading-screen">
        <Skeleton className="loading-mark" />
        <Skeleton className="loading-line" />
      </div>
    );
  const user = me.data;
  if (!user && !["/login", "/signup"].includes(location.pathname))
    return <Navigate to="/login" replace />;
  if (
    user &&
    !user.profile.onboarding_completed &&
    location.pathname !== "/onboarding"
  )
    return <Navigate to="/onboarding" replace />;
  if (
    user &&
    user.profile.onboarding_completed &&
    ["/login", "/signup", "/onboarding"].includes(location.pathname)
  )
    return <Navigate to="/" replace />;
  if (location.pathname === "/signup") return <AuthScreen mode="signup" />;
  if (location.pathname === "/login") return <AuthScreen mode="login" />;
  if (location.pathname === "/onboarding" && user)
    return <Onboarding me={user} />;
  return user ? <Shell me={user} /> : null;
}
