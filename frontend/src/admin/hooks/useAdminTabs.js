import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { DEFAULT_ADMIN_RESOURCE, resourceDefinitions } from "../../adminResources.js";
import { resourceKeyToPath } from "../routes/resourcePaths.js";

function buildTab(resourceKey) {
  const path = resourceKeyToPath(resourceKey);
  const label = resourceDefinitions[resourceKey]?.label ?? resourceKey;
  return { key: path, label, resourceKey };
}

/** 已打开页面标签：随路由追加标签，点击切换，可关闭（至少保留 1 个）。 */
export function useAdminTabs(activeResource) {
  const navigate = useNavigate();
  const activePath = resourceKeyToPath(activeResource);
  const [tabs, setTabs] = useState(() => [buildTab(activeResource)]);

  useEffect(() => {
    setTabs((previous) => {
      if (previous.some((tab) => tab.key === activePath)) {
        return previous;
      }
      return [...previous, buildTab(activeResource)];
    });
  }, [activeResource, activePath]);

  const onTabChange = useCallback(
    (key) => {
      navigate(key);
    },
    [navigate],
  );

  const onTabEdit = useCallback(
    (targetKey, action) => {
      if (action !== "remove") {
        return;
      }

      setTabs((previous) => {
        if (previous.length <= 1) {
          return previous;
        }

        const targetIndex = previous.findIndex((tab) => tab.key === targetKey);
        const nextTabs = previous.filter((tab) => tab.key !== targetKey);

        if (targetKey === activePath) {
          const fallback =
            nextTabs[Math.min(targetIndex, nextTabs.length - 1)] ??
            nextTabs[nextTabs.length - 1] ??
            buildTab(DEFAULT_ADMIN_RESOURCE);
          navigate(fallback.key);
        }

        return nextTabs;
      });
    },
    [activePath, navigate],
  );

  const tabItems = tabs.map((tab) => ({
    key: tab.key,
    label: tab.label,
    resourceKey: tab.resourceKey,
    closable: tabs.length > 1,
  }));
  return {
    activeKey: activePath,
    onTabChange,
    onTabEdit,
    tabItems,
  };
}
