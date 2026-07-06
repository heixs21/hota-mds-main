import { Menu } from "antd";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  buildAdminMenuItems,
  DEFAULT_ADMIN_MENU_OPEN_KEYS,
  getAdminMenuNestedOpenKeys,
  getInitialAdminMenuOpenKeys,
} from "./adminMenu.js";
import { resourceKeyToPath } from "../routes/resourcePaths.js";

export default function AdminSidebar({ activeResource, collapsed = false }) {
  const navigate = useNavigate();
  const menuItems = useMemo(() => buildAdminMenuItems(), []);
  const selectedKeys = useMemo(() => [resourceKeyToPath(activeResource)], [activeResource]);
  const [openKeys, setOpenKeys] = useState(() => getInitialAdminMenuOpenKeys(activeResource));
  const prevCollapsedRef = useRef(collapsed);

  useEffect(() => {
    setOpenKeys((previous) => {
      const required = getAdminMenuNestedOpenKeys(activeResource);
      if (required.length === 0) {
        return previous;
      }
      return Array.from(new Set([...previous, ...required]));
    });
  }, [activeResource]);

  useEffect(() => {
    if (prevCollapsedRef.current && !collapsed) {
      setOpenKeys((previous) =>
        Array.from(new Set([...previous, ...DEFAULT_ADMIN_MENU_OPEN_KEYS, ...getAdminMenuNestedOpenKeys(activeResource)])),
      );
    }
    prevCollapsedRef.current = collapsed;
  }, [activeResource, collapsed]);

  return (
    <div className="admin-sidebar">
      <Menu
        inlineCollapsed={collapsed}
        items={menuItems}
        mode="inline"
        openKeys={openKeys}
        selectedKeys={selectedKeys}
        style={{ borderInlineEnd: "none", flex: 1, overflow: "auto" }}
        onClick={({ key }) => {
          if (key.startsWith("/admin/")) {
            navigate(key);
          }
        }}
        onOpenChange={setOpenKeys}
      />
    </div>
  );
}
