import { theme } from "antd";

export function buildAdminAntdTheme(mode) {
  const isDark = mode === "dark";

  return {
    algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: "#5e6ad2",
      colorInfo: "#5e6ad2",
      borderRadius: 8,
      borderRadiusLG: 12,
      fontFamily:
        '"Inter", "SF Pro Display", -apple-system, system-ui, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
    },
    components: {
      Layout: {
        headerBg: isDark ? "#0f1011" : "#ffffff",
        bodyBg: isDark ? "#08090a" : "#f0f2f5",
        siderBg: isDark ? "#0f1011" : "#ffffff",
      },
      Menu: {
        itemBorderRadius: 6,
        groupTitleColor: isDark ? "#5c6068" : "#9ca3af",
      },
    },
  };
}
