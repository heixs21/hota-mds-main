import { useEffect, useMemo, useState } from "react";

import { DEFAULT_ADMIN_RESOURCE } from "../adminResources.js";
import { buildActiveResourceStorageKey, pickValidResource } from "./adminUtils.js";
import { ResourceEditor } from "./ResourceEditor.jsx";
import { ResourceSidebar } from "./sidebar/ResourceSidebar.jsx";

export default function AdminConsole({ currentUser, navigate, onLogout, onUnauthorized, theme, onToggleTheme, token }) {
  const activeResourceStorageKey = useMemo(
    () => buildActiveResourceStorageKey(currentUser?.username),
    [currentUser?.username],
  );
  const [activeResource, setActiveResource] = useState(() => {
    const saved = window.localStorage.getItem(activeResourceStorageKey);
    return pickValidResource(saved || DEFAULT_ADMIN_RESOURCE);
  });

  useEffect(() => {
    const saved = window.localStorage.getItem(activeResourceStorageKey);
    setActiveResource(pickValidResource(saved || DEFAULT_ADMIN_RESOURCE));
  }, [activeResourceStorageKey]);

  useEffect(() => {
    window.localStorage.setItem(activeResourceStorageKey, pickValidResource(activeResource));
  }, [activeResource, activeResourceStorageKey]);

  return (
    <main className="admin-shell">
      <header className="admin-header">
        <div>
          <p className="eyebrow">HOTA MDS</p>
          <h1>后台管理控制台</h1>
          <p>当前已接入 M2 最小后台能力，供管理员维护基础台账、展示配置、参数配置和数据源配置。</p>
        </div>
        <div className="header-actions">
          <div className="admin-identity">
            <strong>{currentUser.displayName}</strong>
            <span>{currentUser.username}</span>
          </div>
          <button className="ghost-button" onClick={onLogout} type="button">
            退出登录
          </button>
        </div>
      </header>

      <div className="admin-layout">
        <ResourceSidebar
          activeResource={activeResource}
          onChange={setActiveResource}
          theme={theme}
          onToggleTheme={onToggleTheme}
        />
        <ResourceEditor activeResource={activeResource} onUnauthorized={onUnauthorized} token={token} />
      </div>
    </main>
  );
}
