import { BrowserRouter, Route, Routes, useParams } from "react-router-dom";
import { lazy, Suspense } from "react";
import { Spin } from "antd";

import PlaceholderScreen from "./PlaceholderScreen.jsx";
import ScreenDisplay from "./ScreenDisplay.jsx";

const AdminApp = lazy(() => import("./AdminApp.jsx"));

function ScreenLeftRoute() {
  const { areaCode } = useParams();
  return <ScreenDisplay areaCode={decodeURIComponent(areaCode)} screenKey="left" />;
}

function ScreenRightRoute() {
  const { areaCode } = useParams();
  return <ScreenDisplay areaCode={decodeURIComponent(areaCode)} screenKey="right" />;
}

function HomeRoute() {
  return (
    <PlaceholderScreen
      route={{
        title: "和泰智造数屏系统",
        subtitle: "当前可访问左右屏展示页和后台管理页。",
      }}
    />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={
            <Suspense
              fallback={
                <main className="login-page">
                  <div className="login-bg-pattern" aria-hidden="true" />
                  <div className="login-container login-container--checking">
                    <Spin size="large" />
                  </div>
                </main>
              }
            >
              <AdminApp />
            </Suspense>
          }
          path="/admin/*"
        />
        <Route element={<ScreenLeftRoute />} path="/screen/:areaCode/left" />
        <Route element={<ScreenRightRoute />} path="/screen/:areaCode/right" />
        <Route element={<HomeRoute />} path="*" />
      </Routes>
    </BrowserRouter>
  );
}
