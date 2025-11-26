import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./globals.css";
// @ts-expect-error - virtual module
import { registerSW } from 'virtual:pwa-register';

// Register Service Worker
registerSW({
  onNeedRefresh() {
    // Show a prompt to user to refresh
    if (confirm("New content available. Reload?")) {
      window.location.reload();
    }
  },
  onOfflineReady() {
    console.log("App is ready for offline use.");
  },
});

createRoot(document.getElementById("root")!).render(<App />);
