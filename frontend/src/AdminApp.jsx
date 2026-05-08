import { useEffect, useState, useCallback } from "react";

import { ADMIN_TOKEN_STORAGE_KEY, apiRequest } from "./adminApi.js";
import AdminConsole from "./AdminConsole.jsx";


function LoginPage({ isSubmitting, errorMessage, onSubmit, password, setPassword, setUsername, username }) {
  return (
    <main className="login-page">
      <div className="login-bg-pattern" aria-hidden="true" />
      <div className="login-container">
        <div className="login-brand">
          <div className="brand-icon">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect width="48" height="48" rx="12" fill="#5e6ad2" />
              <path d="M14 16h8v4h4v-4h8v16h-8v-4h-4v4h-8V16z" fill="#fff" fillOpacity="0.9" />
              <path d="M18 24h12v2H18v-2z" fill="#5e6ad2" />
            </svg>
          </div>
          <h1 className="brand-title">和泰智造数屏系统</h1>
          <p className="brand-subtitle">HOTA Manufacturing Digital Screen</p>
        </div>

        <div className="login-card">
          <div className="login-card-header">
            <h2>后台管理登录</h2>
            <p>请输入管理员账号和密码以访问后台</p>
          </div>

          <form className="login-card-form" onSubmit={onSubmit}>
            <div className="form-group">
              <label htmlFor="login-username">管理员账号</label>
              <div className="input-wrapper">
                <svg className="input-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path d="M10 10a4 4 0 100-8 4 4 0 000 8zm-7 8a7 7 0 0114 0H3z" />
                </svg>
                <input
                  id="login-username"
                  autoComplete="username"
                  name="username"
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="请输入管理员账号"
                  value={username}
                  autoFocus
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="login-password">密码</label>
              <div className="input-wrapper">
                <svg className="input-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                <input
                  id="login-password"
                  autoComplete="current-password"
                  name="password"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="请输入密码"
                  type="password"
                  value={password}
                />
              </div>
            </div>

            {errorMessage && (
              <div className="login-error" role="alert">
                <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span>{errorMessage}</span>
              </div>
            )}

            <button className="login-submit" disabled={isSubmitting} type="submit">
              {isSubmitting ? (
                <>
                  <span className="login-spinner" aria-hidden="true" />
                  <span>登录中...</span>
                </>
              ) : (
                "登 录"
              )}
            </button>
          </form>
        </div>

        <p className="login-footer">
          <span>和泰智造</span>
          <span className="login-footer-dot" aria-hidden="true" />
          <span>HOTA MDS v1.0</span>
        </p>
      </div>
    </main>
  );
}


const THEME_STORAGE_KEY = "admin-theme";
const ACTIVE_RESOURCE_STORAGE_PREFIX = "hota-mds-admin-active-resource";

function buildActiveResourceStorageKey(username) {
  return `${ACTIVE_RESOURCE_STORAGE_PREFIX}:${username || "anonymous"}`;
}

function AdminApp({ pathname, navigate }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(() => window.sessionStorage.getItem(ADMIN_TOKEN_STORAGE_KEY) ?? "");
  const [currentUser, setCurrentUser] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [theme, setTheme] = useState(() => window.localStorage.getItem(THEME_STORAGE_KEY) || "dark");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  const clearSession = useCallback((navigateToLogin = false) => {
    window.sessionStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    setToken("");
    setCurrentUser(null);
    setPassword("");
    if (navigateToLogin) {
      navigate("/admin/login", true);
    }
  }, [navigate]);

  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      return;
    }

    let cancelled = false;

    async function fetchCurrentAdmin() {
      try {
        const payload = await apiRequest("/api/admin/auth/me", { token });
        if (!cancelled) {
          setCurrentUser(payload.data.user);
          if (pathname === "/admin/login") {
            navigate("/admin/console", true);
          }
        }
      } catch {
        if (!cancelled) {
          clearSession();
        }
      }
    }

    fetchCurrentAdmin();

    return () => {
      cancelled = true;
    };
  }, [token, pathname, navigate, clearSession]);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const payload = await apiRequest("/api/admin/auth/login", {
        method: "POST",
        body: { username, password },
      });
      const nextToken = payload.data.access_token;

      window.sessionStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, nextToken);
      setToken(nextToken);
      setPassword("");
      navigate("/admin/console", true);
    } catch (error) {
      setErrorMessage(error.message || "登录失败，请检查账号和密码。");
      clearSession();
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLogout() {
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
  }

  if (currentUser) {
    return (
      <AdminConsole
        currentUser={currentUser}
        navigate={navigate}
        onLogout={handleLogout}
        onUnauthorized={() => clearSession(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
        token={token}
      />
    );
  }

  return (
    <LoginPage
      isSubmitting={isSubmitting}
      errorMessage={errorMessage}
      onSubmit={handleSubmit}
      password={password}
      setPassword={setPassword}
      setUsername={setUsername}
      username={username}
    />
  );
}

export default AdminApp;
