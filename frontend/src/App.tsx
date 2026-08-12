import type { Session } from "@supabase/supabase-js";
import { SignOut } from "@phosphor-icons/react";
import { useCallback, useEffect, useState } from "react";
import Briefing from "./pages/Briefing";
import Dashboard from "./pages/Dashboard";
import Decisions from "./pages/Decisions";
import Login from "./pages/Login";
import MeetingDetail from "./pages/MeetingDetail";
import Review from "./pages/Review";
import Settings from "./pages/Settings";
import Tasks from "./pages/Tasks";
import Upload from "./pages/Upload";
import { apiFetch, resetCsrfToken } from "./lib/api";
import { supabase } from "./lib/supabaseClient";

function useSession(): Session | null | undefined {
  // undefined = jeszcze nie sprawdzono, null = brak sesji (pokaż login)
  const [session, setSession] = useState<Session | null | undefined>(undefined);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  return session;
}

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
        "rounded-md px-3 py-1.5 text-sm font-medium transition-colors " +
        (active
          ? "bg-zinc-800 text-white"
          : "text-zinc-400 hover:text-zinc-100")
      }
    >
      {children}
    </a>
  );
}

function App() {
  const session = useSession();
  const [path, navigate] = useRoute();
  const reviewMatch = path.match(/^\/meetings\/([^/]+)\/review$/);
  const meetingMatch = path.match(/^\/meetings\/([^/]+)$/);

  // Dwie niezależne sesje: Supabase (bramka logowania frontu) i cookie
  // backendu (Google OAuth albo demo). Samo signOut() zostawiało tę drugą
  // aktywną, więc po ponownym zalogowaniu backend widział starą tożsamość.
  const logout = useCallback(async () => {
    await apiFetch("/auth/logout", { method: "POST" }).catch(() => {
      // Sesja backendu mogła już wygasnąć — wylogowanie z Supabase i tak ma się udać.
    });
    resetCsrfToken();
    await supabase.auth.signOut();
  }, []);

  if (session === undefined) {
    return <div className="min-h-screen bg-black" />;
  }
  if (session === null) {
    return <Login />;
  }

  let page: React.ReactNode;
  let wide = false;
  if (path === "/settings") {
    page = <Settings />;
  } else if (path === "/tasks") {
    page = <Tasks />;
    wide = true;
  } else if (path === "/decisions") {
    page = <Decisions />;
    wide = true;
  } else if (path === "/briefing") {
    page = <Briefing />;
  } else if (path === "/upload") {
    page = <Upload onCreated={(id) => navigate(`/meetings/${id}`)} />;
  } else if (reviewMatch) {
    page = <Review meetingId={reviewMatch[1]} navigate={navigate} />;
    wide = true;
  } else if (meetingMatch) {
    page = <MeetingDetail meetingId={meetingMatch[1]} navigate={navigate} />;
  } else {
    page = <Dashboard navigate={navigate} />;
  }

  return (
    <div className="min-h-screen bg-black">
      <nav className="sticky top-0 z-10 flex items-center gap-2 border-b border-zinc-800 bg-black/95 px-8 py-3 backdrop-blur">
        <span className="mr-4 text-sm font-semibold tracking-tight text-white">
          Analiza spotkań
        </span>
        <NavLink to="/" path={path} navigate={navigate}>
          Dashboard
        </NavLink>
        <NavLink to="/upload" path={path} navigate={navigate}>
          Nowe spotkanie
        </NavLink>
        <NavLink to="/tasks" path={path} navigate={navigate}>
          Zadania
        </NavLink>
        <NavLink to="/decisions" path={path} navigate={navigate}>
          Decyzje
        </NavLink>
        <NavLink to="/briefing" path={path} navigate={navigate}>
          Briefing
        </NavLink>
        <NavLink to="/settings" path={path} navigate={navigate}>
          Ustawienia
        </NavLink>
        <button
          onClick={logout}
          className="ml-auto flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-zinc-400 transition-transform hover:text-zinc-100 active:scale-[0.98]"
        >
          <SignOut size={16} weight="bold" />
          Wyloguj
        </button>
      </nav>
      <div className={(wide ? "max-w-4xl" : "max-w-2xl") + " mx-auto px-4 py-10"}>{page}</div>
    </div>
  );
}

export default App;
