import { useCallback, useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";
import MeetingDetail from "./pages/MeetingDetail";
import Settings from "./pages/Settings";
import Upload from "./pages/Upload";

// Router-lite: kilka stron na razie nie uzasadnia jeszcze dociągania
// react-router-dom. Rozbuduje się w kolejnych etapach (§11 SPEC.md), gdy
// przybędzie więcej ekranów.
function useRoute(): [string, (to: string) => void] {
  const [path, setPath] = useState(() => window.location.pathname);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const navigate = useCallback((to: string) => {
    window.history.pushState({}, "", to);
    setPath(to);
  }, []);

  return [path, navigate];
}

function NavLink({
  to,
  path,
  navigate,
  children,
}: {
  to: string;
  path: string;
  navigate: (to: string) => void;
  children: React.ReactNode;
}) {
  const active = path === to;
  return (
    <a
      href={to}
      onClick={(e) => {
        e.preventDefault();
        navigate(to);
      }}
      className={
        active
          ? "font-medium text-gray-900"
          : "text-gray-500 hover:text-gray-900"
      }
    >
      {children}
    </a>
  );
}

function App() {
  const [path, navigate] = useRoute();
  const meetingMatch = path.match(/^\/meetings\/([^/]+)$/);

  let page: React.ReactNode;
  if (path === "/settings") {
    page = <Settings />;
  } else if (path === "/upload") {
    page = <Upload onCreated={(id) => navigate(`/meetings/${id}`)} />;
  } else if (meetingMatch) {
    page = <MeetingDetail meetingId={meetingMatch[1]} />;
  } else {
    page = <Dashboard navigate={navigate} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="flex items-center gap-6 border-b border-gray-200 bg-white px-8 py-4">
        <NavLink to="/" path={path} navigate={navigate}>
          Dashboard
        </NavLink>
        <NavLink to="/upload" path={path} navigate={navigate}>
          Nowe spotkanie
        </NavLink>
        <NavLink to="/settings" path={path} navigate={navigate}>
          Ustawienia
        </NavLink>
      </nav>
      <div className="max-w-2xl mx-auto py-10 px-4">{page}</div>
    </div>
  );
}

export default App;
