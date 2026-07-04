import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles/global.css";
import "./styles/admin.css";
import "./styles/screen.css";


createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
