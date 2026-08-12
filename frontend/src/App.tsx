import type { Session } from "@supabase/supabase-js";
import { List, SignOut, X } from "@phosphor-icons/react";
import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import { apiFetch, resetCsrfToken } from "./lib/api";
import { supabase } from "./lib/supabaseClient";

// Login i Dashboard zostają eager: Login trzeba pokazać natychmiast, zanim
// wiadomo, czy sesja istnieje, a Dashboard to domyślna trasa („/") — prawie
// każdy tu ląduje. Lazy dla Dashboardu kupowałoby ~8kB kosztem dodatkowego
// round-tripu sieciowego na PIERWSZYM ekranie, dokładnie tam, gdzie PRODUCT.md
// każe traktować szybkość pierwszego wrażenia priorytetowo. Pozostałych sześć
// ekranów wymaga jawnej nawigacji, więc ładuje się dopiero na żądanie.
const Briefing = lazy(() => import("./pages/Briefing"));
const Decisions = lazy(() => import("./pages/Decisions"));
const MeetingDetail = lazy(() => import("./pages/MeetingDetail"));
const Review = lazy(() => import("./pages/Review"));
const Settings = lazy(() => import("./pages/Settings"));
const Tasks = lazy(() => import("./pages/Tasks"));
const Upload = lazy(() => import("./pages/Upload"));

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
  dense = false,
}: {
  to: string;
  path: string;
  navigate: (to: string) => void;
  children: React.ReactNode;
  // Drawer mobilny potrzebuje większego celu dotykowego niż pigułka
  // w poziomym pasku desktopowym — sama logika kolorów zostaje wspólna.
  dense?: boolean;
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
        "rounded-md text-sm font-medium transition-colors " +
        (dense ? "px-3 py-2.5 " : "px-3 py-1.5 ") +
        // Sygnał operacyjny (niebieski) oznacza „to jest aktywne" —
        // DESIGN.md, Zasada Odczytu. Sama szarość (bg-zinc-800) tego nie
        // mówiła; teraz aktywna zakładka jest odczytem stanu, nie dekoracją.
        (active
          ? "bg-blue-500/15 text-blue-400"
          : "text-zinc-400 hover:text-zinc-100")
      }
    >
      {children}
    </a>
  );
}

const NAV_ITEMS = [
  { to: "/", label: "Dashboard" },
  { to: "/upload", label: "Nowe spotkanie" },
  { to: "/tasks", label: "Zadania" },
  { to: "/decisions", label: "Decyzje" },
  { to: "/briefing", label: "Briefing" },
  { to: "/settings", label: "Ustawienia" },
];

function App() {
  const session = useSession();
  const [path, navigate] = useRoute();
  const [menuOpen, setMenuOpen] = useState(false);
  const reviewMatch = path.match(/^\/meetings\/([^/]+)\/review$/);
  const meetingMatch = path.match(/^\/meetings\/([^/]+)$/);

  // Sześć linków w jednym rzędzie potrzebuje 738px i nie zwija się —
  // na telefonie (375px) pasek nawigacji wystawał 363px poza ekran.
  // Poniżej md nawigacja chowa się za hamburgerem; zamykamy ją przy każdej
  // zmianie trasy, żeby kolejny ekran nie startował z otwartym menu.
  useEffect(() => {
    setMenuOpen(false);
  }, [path]);

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
    page = <Tasks navigate={navigate} />;
    wide = true;
  } else if (path === "/decisions") {
    page = <Decisions navigate={navigate} />;
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
      {/* Niewidoczna, dopóki nie dostanie fokusa klawiaturą — pozwala
          pominąć siedem stopów tabulacji w nawigacji (sześć linków +
          wylogowanie) i przejść od razu do treści strony. */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-20 focus:rounded-md focus:bg-blue-600 focus:px-3 focus:py-1.5 focus:text-sm focus:font-medium focus:text-white"
      >
        Przejdź do treści
      </a>
      <nav className="sticky top-0 z-10 border-b border-zinc-800 bg-black/95 backdrop-blur">
        <div className="flex items-center gap-2 px-4 py-3 sm:px-8">
          <span className="mr-4 text-sm font-semibold tracking-tight text-white">
            Analiza spotkań
          </span>
          <div className="hidden items-center gap-2 md:flex">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} path={path} navigate={navigate}>
                {item.label}
              </NavLink>
            ))}
          </div>
          <button
            onClick={logout}
            className="ml-auto hidden items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-zinc-400 transition-transform hover:text-zinc-100 active:scale-[0.98] md:flex"
          >
            <SignOut size={16} weight="bold" />
            Wyloguj
          </button>
          {/* 44px w obie strony — próg dotykowy z audytu (AAA, 2.5.5); jedyny
              kontrolny element w aplikacji celowo większy od reszty przycisków. */}
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-label={menuOpen ? "Zamknij menu" : "Otwórz menu"}
            aria-expanded={menuOpen}
            className="ml-auto flex h-11 w-11 items-center justify-center rounded-md text-zinc-400 transition-transform active:scale-[0.98] md:hidden"
          >
            {menuOpen ? <X size={20} weight="bold" /> : <List size={20} weight="bold" />}
          </button>
        </div>
        {menuOpen && (
          <div className="flex flex-col gap-1 border-t border-zinc-800 px-4 py-3 md:hidden">
            {NAV_ITEMS.map((item) => (
              <NavLink key={item.to} to={item.to} path={path} navigate={navigate} dense>
                {item.label}
              </NavLink>
            ))}
            <button
              onClick={logout}
              className="mt-1 flex items-center gap-1.5 rounded-md px-3 py-2.5 text-left text-sm font-medium text-zinc-400 transition-transform hover:text-zinc-100 active:scale-[0.98]"
            >
              <SignOut size={16} weight="bold" />
              Wyloguj
            </button>
          </div>
        )}
      </nav>
      <main
        id="main-content"
        tabIndex={-1}
        className={(wide ? "max-w-4xl" : "max-w-2xl") + " mx-auto px-4 py-6 outline-none sm:py-10"}
      >
        {/* Trasy poza Dashboardem ładują się dopiero na żądanie (patrz
            lazy() powyżej) — ten fallback trzyma miejsce na czas pobrania
            chunka. Bez ruchu, zgodnie z DESIGN.md: licznik czasu niesie
            informację, obracające się kółko nie — a to trwa zwykle
            pojedyncze dziesiątki milisekund, więc nawet licznik byłby
            przesadą. */}
        <Suspense fallback={<p className="text-sm text-zinc-400">Wczytywanie…</p>}>
          {page}
        </Suspense>
      </main>
    </div>
  );
}

export default App;
