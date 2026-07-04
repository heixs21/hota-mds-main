import { ConfigProvider, Flex, Spin, message } from "antd";
import zhCN from "antd/locale/zh_CN";
import { useCallback, useEffect, useState } from "react";
import { Navigate, Outlet, Route, Routes, useLocation, useNavigate } from "react-router-dom";

import { DEFAULT_ADMIN_RESOURCE } from "../adminResources.js";
import { ADMIN_TOKEN_STORAGE_KEY, apiRequest } from "../adminApi.js";
import { humanizeAdminApiError } from "../adminUserFacingMessages.js";
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
import { adminTheme } from "./adminTheme.js";
import { buildActiveResourceStorageKey } from "./adminUtils.js";

function SessionCheckingView() {
  return (
    <Flex align="center" className="login-page" justify="center">
      <Spin size="large" />
    </Flex>
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
  const { currentUser, sessionChecked, token, loginIsSubmitting, onLoginSubmit } = useAdminSession();
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

  return <LoginPage isSubmitting={loginIsSubmitting} onSubmit={onLoginSubmit} />;
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
  const [token, setToken] = useState(() => window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ?? "");
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionChecked, setSessionChecked] = useState(() => !window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY));
  const [loginIsSubmitting, setLoginIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const clearSession = useCallback(
    (navigateToLogin = false) => {
      window.sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
      setToken("");
      setCurrentUser(null);
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
    async ({ username, password }) => {
      setLoginIsSubmitting(true);

      try {
        const payload = await apiRequest("/api/admin/auth/login", {
          method: "POST",
          body: { username, password },
        });
        const nextToken = payload.data.access_token;
        const user = payload.data.user;

        window.sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, nextToken);
        setToken(nextToken);
        setCurrentUser(user);
        setSessionChecked(true);
        message.success("登录成功");
        navigate(getDefaultAdminPath(user.username), { replace: true });
      } catch (error) {
        message.error(humanizeAdminApiError(error, [], { fallback: "登录失败，请检查账号和密码。" }));
        clearSession();
      } finally {
        setLoginIsSubmitting(false);
      }
    },
    [clearSession, navigate],
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

  const sessionValue = {
    currentUser,
    sessionChecked,
    token,
    onLogout,
    onUnauthorized: () => clearSession(true),
    loginIsSubmitting,
    onLoginSubmit,
  };

  return (
    <ConfigProvider locale={zhCN} theme={adminTheme}>
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
