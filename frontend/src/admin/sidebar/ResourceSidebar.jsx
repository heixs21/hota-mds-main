import { useMemo, useState } from "react";

import { ADMIN_MENU_GROUPS, resourceDefinitions } from "../../adminResources.js";

function ThemeIcon({ theme }) {
  if (theme === "light") {
    return (
      <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function SubmenuChevron({ expanded }) {
  return (
    <svg className={`submenu-chevron${expanded ? " expanded" : ""}`} viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M5 6l3 3 3-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * 左侧导航：按 adminResources.ADMIN_MENU_GROUPS（基础台账 / 大屏配置 / 系统设置）渲染分组。
 */
export function ResourceSidebar({ activeResource, onChange, theme, onToggleTheme }) {
  const initialExpanded = useMemo(() => {
    const set = new Set();
    for (const group of ADMIN_MENU_GROUPS) {
      for (const item of group.items) {
        if (item && typeof item === "object" && item.kind === "submenu") {
          if (item.children?.includes(activeResource)) {
            set.add(item.id);
          }
        }
      }
    }
    return set;
  }, [activeResource]);

  const [expandedSubmenus, setExpandedSubmenus] = useState(initialExpanded);

  function toggleSubmenu(submenuId) {
    setExpandedSubmenus((prev) => {
      const next = new Set(prev);
      if (next.has(submenuId)) {
        next.delete(submenuId);
      } else {
        next.add(submenuId);
      }
      return next;
    });
  }

  function renderResourceTab(resourceKey, extraClass = "") {
    const resourceDefinition = resourceDefinitions[resourceKey];
    if (!resourceDefinition) {
      return null;
    }
    return (
      <button
        className={`resource-tab${activeResource === resourceKey ? " active" : ""}${extraClass ? ` ${extraClass}` : ""}`}
        key={resourceKey}
        onClick={() => onChange(resourceKey)}
        type="button"
      >
        {resourceDefinition.label}
      </button>
    );
  }

  return (
    <nav className="resource-nav" aria-label="后台资源">
      {ADMIN_MENU_GROUPS.map((group) => (
        <div className="resource-nav-group" key={group.id}>
          <div className="resource-nav-group-title" id={`nav-group-${group.id}`}>
            {group.label}
          </div>
          <div aria-labelledby={`nav-group-${group.id}`} className="resource-nav-group-items" role="group">
            {group.items.map((item) => {
              if (typeof item === "string") {
                return renderResourceTab(item);
              }
              if (item && item.kind === "submenu") {
                const expanded = expandedSubmenus.has(item.id);
                const hasActiveChild = item.children?.includes(activeResource);
                return (
                  <div className="resource-submenu" key={item.id}>
                    <button
                      type="button"
                      className={`resource-tab resource-submenu-toggle${hasActiveChild ? " active-parent" : ""}`}
                      aria-expanded={expanded}
                      onClick={() => toggleSubmenu(item.id)}
                    >
                      <span>{item.label}</span>
                      <SubmenuChevron expanded={expanded} />
                    </button>
                    {expanded ? (
                      <div className="resource-submenu-children">
                        {item.children.map((childKey) => renderResourceTab(childKey, "resource-tab--child"))}
                      </div>
                    ) : null}
                  </div>
                );
              }
              return null;
            })}
          </div>
        </div>
      ))}
      <div className="nav-footer">
        <button className="theme-toggle" onClick={onToggleTheme} type="button">
          <ThemeIcon theme={theme} />
          <span>{theme === "dark" ? "切换明亮主题" : "切换暗色主题"}</span>
        </button>
      </div>
    </nav>
  );
}
