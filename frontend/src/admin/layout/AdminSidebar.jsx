import { Menu } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { buildAdminMenuItems, getAdminMenuNestedOpenKeys, getInitialAdminMenuOpenKeys } from "./adminMenu.js";
import { resourceKeyToPath } from "../routes/resourcePaths.js";

export default function AdminSidebar({ activeResource }) {
  const navigate = useNavigate();
  const menuItems = useMemo(() => buildAdminMenuItems(), []);
  const selectedKeys = useMemo(() => [resourceKeyToPath(activeResource)], [activeResource]);
  const [openKeys, setOpenKeys] = useState(() => getInitialAdminMenuOpenKeys(activeResource));

  useEffect(() => {
    setOpenKeys((previous) => {
      const required = getAdminMenuNestedOpenKeys(activeResource);
      if (required.length === 0) {
        return previous;
      }
      return Array.from(new Set([...previous, ...required]));
    });
  }, [activeResource]);

  return (
    <div className="admin-sidebar">
      <Menu
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
