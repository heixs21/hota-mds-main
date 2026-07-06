import { createContext, useContext } from "react";

const AdminSessionContext = createContext(null);

export function AdminSessionProvider({ children, value }) {
  return <AdminSessionContext.Provider value={value}>{children}</AdminSessionContext.Provider>;
}

export function useAdminSession() {
  const context = useContext(AdminSessionContext);
  if (!context) {
    throw new Error("useAdminSession must be used within AdminSessionProvider");
  }
  return context;
}
