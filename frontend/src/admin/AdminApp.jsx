import { ConfigProvider, Spin } from "antd";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Outlet, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { DEFAULT_ADMIN_RESOURCE } from "../adminResources.js";
import { ADMIN_TOKEN_STORAGE_KEY, apiRequest } from "../adminApi.js";
import LoginPage from "./LoginPage.jsx";
import { AdminSessionProvider, useAdminSession } from "./context/AdminSessionContext.jsx";
import AdminLayout from "./layout/AdminLayout.jsx";
import { ADMIN_RESOURCE_ROUTES } from "./routes/adminRouteRegistry.js";
import {
  ADMIN_LEGACY_CONSOLE_PATH,
  ADMIN_LOGIN_PATH,
  getDefaultAdminPath,
  isAdminResourcePath,
  resourceKeyToPath,
} from "./routes/resourcePaths.js";
import { buildAdminAntdTheme } from "./adminTheme.js";
import { buildActiveResourceStorageKey } from "./adminUtils.js";

const THEME_STORAGE_KEY = "admin-theme";

function SessionCheckingView() {
  return (
    <main className="login-page">
      <div className="login-bg-pattern" aria-hidden="true" />
      <div className="login-container login-container--checking">
        <Spin size="large" />
      </div>
    </main>
  );
}

function RequireAuth() {
  const { currentUser, sessionChecked, token } = useAdminSession();
  const location = useLocation();

  if (!sessionChecked && token) {
    return <SessionCheckingView />;
  }

  if (!currentUser) {
    return <Navigate replace state={{ from: location }} to={ADMIN_LOGIN_PATH} />;
  }

  return <Outlet />;
}

function AdminLoginRoute() {
  const {
    currentUser,
    sessionChecked,
    token,
    loginErrorMessage,
    loginIsSubmitting,
    loginPassword,
    loginUsername,
    onLoginSubmit,
    setLoginPassword,
    setLoginUsername,
  } = useAdminSession();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!currentUser || !sessionChecked) {
      return;
    }

    const fromPath = location.state?.from?.pathname;
    let target = getDefaultAdminPath(currentUser.username);

    if (fromPath && fromPath !== ADMIN_LOGIN_PATH) {
      if (isAdminResourcePath(fromPath)) {
        target = fromPath;
      } else if (fromPath === ADMIN_LEGACY_CONSOLE_PATH) {
        target = getDefaultAdminPath(currentUser.username);
      }
    }

    navigate(target, { replace: true });
  }, [currentUser, sessionChecked, location.state, navigate]);

  if (!sessionChecked && token) {
    return <SessionCheckingView />;
  }

  if (currentUser) {
    return null;
  }

  return (
    <LoginPage
      errorMessage={loginErrorMessage}
      isSubmitting={loginIsSubmitting}
      onSubmit={onLoginSubmit}
      password={loginPassword}
      setPassword={setLoginPassword}
      setUsername={setLoginUsername}
      username={loginUsername}
    />
  );
}

function AdminIndexRedirect() {
  const { currentUser } = useAdminSession();
  return <Navigate replace to={getDefaultAdminPath(currentUser?.username)} />;
}

function LegacyConsoleRedirect() {
  const { currentUser } = useAdminSession();
  return <Navigate replace to={getDefaultAdminPath(currentUser?.username)} />;
}

function UnknownAdminRedirect() {
  return <Navigate replace to={resourceKeyToPath(DEFAULT_ADMIN_RESOURCE)} />;
}

export default function AdminApp() {
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [token, setToken] = useState(() => window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ?? "");
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionChecked, setSessionChecked] = useState(() => !window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY));
  const [loginErrorMessage, setLoginErrorMessage] = useState("");
  const [loginIsSubmitting, setLoginIsSubmitting] = useState(false);
  const [theme, setTheme] = useState(() => window.localStorage.getItem(THEME_STORAGE_KEY) || "dark");
  const navigate = useNavigate();

  const antdTheme = useMemo(() => buildAdminAntdTheme(theme), [theme]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const clearSession = useCallback(
    (navigateToLogin = false) => {
      window.sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
      setToken("");
      setCurrentUser(null);
      setLoginPassword("");
      setSessionChecked(true);
      if (navigateToLogin) {
        navigate(ADMIN_LOGIN_PATH, { replace: true });
      }
    },
    [navigate],
  );

  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      setSessionChecked(true);
      return;
    }

    if (currentUser) {
      setSessionChecked(true);
      return;
    }

    let cancelled = false;
    setSessionChecked(false);

    async function restoreSession() {
      try {
        const payload = await apiRequest("/api/admin/auth/me", { token });
        if (!cancelled) {
          setCurrentUser(payload.data.user);
        }
      } catch {
        if (!cancelled) {
          clearSession();
        }
      } finally {
        if (!cancelled) {
          setSessionChecked(true);
        }
      }
    }

    restoreSession();

    return () => {
      cancelled = true;
    };
  }, [token, currentUser, clearSession]);

  const onLoginSubmit = useCallback(
    async (event) => {
      event.preventDefault();
      setLoginIsSubmitting(true);
      setLoginErrorMessage("");

      try {
        const payload = await apiRequest("/api/admin/auth/login", {
          method: "POST",
          body: { username: loginUsername, password: loginPassword },
        });
        const nextToken = payload.data.access_token;
        const user = payload.data.user;

        window.sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, nextToken);
        setToken(nextToken);
        setCurrentUser(user);
        setSessionChecked(true);
        setLoginPassword("");
        navigate(getDefaultAdminPath(user.username), { replace: true });
      } catch (error) {
        setLoginErrorMessage(error.message || "登录失败，请检查账号和密码。");
        clearSession();
      } finally {
        setLoginIsSubmitting(false);
      }
    },
    [clearSession, loginPassword, loginUsername, navigate],
  );

  const onLogout = useCallback(async () => {
    const usernameForCleanup = currentUser?.username;
    try {
      await apiRequest("/api/admin/auth/logout/", { method: "POST", token });
    } catch {
      // Best-effort logout; clear local session regardless
    }
    if (usernameForCleanup) {
      window.localStorage.removeItem(buildActiveResourceStorageKey(usernameForCleanup));
    }
    clearSession(true);
  }, [clearSession, currentUser?.username, token]);

  const sessionValue = useMemo(
    () => ({
      currentUser,
      sessionChecked,
      token,
      theme,
      onToggleTheme: toggleTheme,
      onLogout,
      onUnauthorized: () => clearSession(true),
      loginUsername,
      setLoginUsername,
      loginPassword,
      setLoginPassword,
      loginErrorMessage,
      loginIsSubmitting,
      onLoginSubmit,
    }),
    [
      clearSession,
      currentUser,
      loginErrorMessage,
      loginIsSubmitting,
      loginPassword,
      loginUsername,
      onLoginSubmit,
      onLogout,
      sessionChecked,
      theme,
      toggleTheme,
      token,
    ],
  );

  return (
    <ConfigProvider theme={antdTheme}>
      <AdminSessionProvider value={sessionValue}>
        <Routes>
          <Route element={<AdminLoginRoute />} path="login" />
          <Route element={<RequireAuth />}>
            <Route element={<AdminLayout />}>
              <Route element={<AdminIndexRedirect />} index />
              <Route element={<LegacyConsoleRedirect />} path="console" />
              {ADMIN_RESOURCE_ROUTES.map(({ slug, Component }) => (
                <Route element={<Component />} key={slug} path={slug} />
              ))}
              <Route element={<UnknownAdminRedirect />} path="*" />
            </Route>
          </Route>
          <Route element={<Navigate replace to={ADMIN_LOGIN_PATH} />} path="*" />
        </Routes>
      </AdminSessionProvider>
    </ConfigProvider>
  );
}
