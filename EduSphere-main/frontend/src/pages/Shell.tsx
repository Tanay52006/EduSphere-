import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "react-router-dom";
import type { Me } from "../lib/api";
import { api } from "../lib/api";
import { applyTheme, getInitialTheme, type Theme } from "../lib/theme";
import { Toast } from "../components/ui";
import { EmptyStateScreen } from "./EmptyStateScreen";
import { Home } from "./Home";
import { Library } from "./Library";
import { Games } from "./Games";
import { GamePlay } from "./GamePlay";
import { Progress } from "./Progress";
import { ChainPlay } from "./ChainPlay";
import { ActivityPlay } from "./ActivityPlay";
import { ArenaIcon } from "../components/ArenaIcon";

const navItems = [
  { label: "Home", icon: "home", path: "/" },
  { label: "Library", icon: "library", path: "/library" },
  { label: "Paths", icon: "paths", path: "/paths" },
  { label: "Games", icon: "games", path: "/games" },
  { label: "Progress", icon: "progress", path: "/progress" },
] as const;

export function Shell({ me }: { me: Me }) {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [collapsed, setCollapsed] = useState(false);
  const [toast, setToast] = useState("");
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  useEffect(() => applyTheme(theme), [theme]);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);
  const logout = async () => {
    await api.logout();
    queryClient.clear();
    queryClient.setQueryData(["me"], null);
    navigate("/login");
  };
  const active =
    (location.pathname.startsWith("/games/") ||
    location.pathname === "/questions"
      ? navItems[3]
      : navItems.find((item) => item.path === location.pathname)) ??
    navItems[0];
  const firstName = me.profile.display_name?.split(" ")[0] || "there";
  return (
    <div
      className={`app-shell ${collapsed ? "sidebar-collapsed" : ""} ${active.path === "/games" || active.path === "/progress" ? "arcade-world" : ""}`}
    >
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">
        <div className="sidebar-top">
          <Link to="/" className="brand">
            <span className="brand-mark">e</span>
            <span>EduSphere</span>
          </Link>
          <button
            className="collapse-button"
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? "→" : "←"}
          </button>
        </div>
        <nav aria-label="Main navigation">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={active.path === item.path ? "active" : ""}
              aria-current={active.path === item.path ? "page" : undefined}
              aria-label={item.label}
            >
              <span className="nav-icon">
                <ArenaIcon name={item.icon} size={21} />
              </span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button
            className="theme-toggle"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <ArenaIcon name={theme === "dark" ? "sun" : "moon"} size={19} />
            <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
          </button>
          <button className="profile-button" onClick={logout}>
            <span className="avatar">{firstName[0].toUpperCase()}</span>
            <span className="profile-name">
              <strong>{me.profile.display_name || "Your profile"}</strong>
              <small>Log out</small>
            </span>
            <span>⋯</span>
          </button>
        </div>
      </aside>
      <nav className="mobile-nav" aria-label="Mobile navigation">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={active.path === item.path ? "active" : ""}
            aria-current={active.path === item.path ? "page" : undefined}
          >
            <span>
              <ArenaIcon name={item.icon} size={22} />
            </span>
            <small>{item.label}</small>
          </Link>
        ))}
      </nav>
      <main className="app-main">
        <header className="app-header">
          <div>
            <span className="breadcrumb">My space / {active.label}</span>
            <h1>{active.label}</h1>
          </div>
          <div className="header-actions">
            <button
              className="mobile-theme-button"
              aria-label={
                theme === "dark"
                  ? "Switch to light mode"
                  : "Switch to dark mode"
              }
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              <ArenaIcon name={theme === "dark" ? "sun" : "moon"} size={19} />
            </button>
            <button
              className="header-avatar"
              aria-label="Log out"
              onClick={logout}
            >
              {firstName[0].toUpperCase()}
            </button>
          </div>
        </header>
        <div id="main-content">
          {location.pathname === "/" ? (
            <Home
              firstName={firstName}
              timezone={me.profile.timezone}
              onToast={setToast}
            />
          ) : location.pathname === "/library" ? (
            <Library />
          ) : location.pathname.startsWith("/games/activity/") ? (
            <ActivityPlay
              key={location.pathname}
              sessionId={location.pathname.split("/")[3]}
            />
          ) : location.pathname.startsWith("/games/chain/") ? (
            <ChainPlay
              key={location.pathname}
              sessionId={location.pathname.split("/")[3]}
            />
          ) : location.pathname === "/games" ? (
            <Games />
          ) : location.pathname.startsWith("/games/play/") ? (
            <GamePlay
              key={location.pathname}
              sessionId={location.pathname.split("/")[3]}
            />
          ) : location.pathname === "/games/practice" ||
            location.pathname === "/questions" ? (
            <Games bankView={location.pathname === "/questions"} />
          ) : location.pathname === "/progress" ? (
            <Progress />
          ) : (
            <EmptyStateScreen title={active.label} icon="◎" />
          )}
        </div>
        {toast && <Toast message={toast} onClose={() => setToast("")} />}
      </main>
    </div>
  );
}
