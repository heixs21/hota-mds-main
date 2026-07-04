import { theme } from "antd";

/** Default light theme; Layout header/sider use light surfaces (antd defaults are dark). */
export const adminTheme = {
  algorithm: theme.defaultAlgorithm,
  components: {
    Layout: {
      headerBg: "#ffffff",
      headerColor: "rgba(0, 0, 0, 0.88)",
      siderBg: "#ffffff",
      triggerBg: "#ffffff",
      triggerColor: "rgba(0, 0, 0, 0.65)",
    },
  },
};
