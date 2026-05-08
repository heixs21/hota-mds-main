import { useEffect, useState } from "react";

import AdminApp from "./AdminApp.jsx";
import PlaceholderScreen from "./PlaceholderScreen.jsx";
import ScreenDisplay from "./ScreenDisplay.jsx";

function usePathname() {
  const [pathname, setPathname] = useState(window.location.pathname);

  useEffect(() => {
    function handlePopState() {
      setPathname(window.location.pathname);
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  function navigate(nextPathname, replace = false) {
    if (replace) {
      window.history.replaceState({}, "", nextPathname);
    } else {
      window.history.pushState({}, "", nextPathname);
    }
    setPathname(nextPathname);
  }

  return [pathname, navigate];
}

function App() {
  const [pathname, navigate] = usePathname();

  if (pathname === "/admin/login" || pathname === "/admin/console") {
    return <AdminApp navigate={navigate} pathname={pathname} />;
  }

  const leftMatch = pathname.match(/^\/screen\/([^/]+)\/left$/);
  if (leftMatch) {
    return <ScreenDisplay areaCode={decodeURIComponent(leftMatch[1])} screenKey="left" />;
  }

  const rightMatch = pathname.match(/^\/screen\/([^/]+)\/right$/);
  if (rightMatch) {
    return <ScreenDisplay areaCode={decodeURIComponent(rightMatch[1])} screenKey="right" />;
  }

  return (
    <PlaceholderScreen
      route={{
        title: "和泰智造数屏系统",
        subtitle: "当前可访问左右屏展示页和后台管理页。",
      }}
    />
  );
}

export default App;
