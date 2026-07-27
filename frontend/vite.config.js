// vite.config.js

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The export must be a function that accepts 'mode'
export default defineConfig(({ mode }) => {
  // 1. Load the environment variables for the current mode.
  // We use '' as the third argument to load ALL variables, not just VITE_ prefixed ones,
  // though VITE_BASE_WS_URL should be loaded regardless.
  const env = loadEnv(mode, process.cwd(), "");

  // 2. Access the variable from the loaded 'env' object.
  const baseWsUrl = env.VITE_BASE_WS_URL;

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 3000,
      proxy: {
        "/ws-api": {
          // 3. Use the variable stored in the constant
          target: baseWsUrl,
          ws: true,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/ws-api/, "/ws"),
          configure: (proxy, _options) => {
            proxy.on("proxyReqWs", (proxyReq, req, socket, options, head) => {
              const url = new URL(req.url, "http://localhost");
              const token = url.searchParams.get("token");
              if (token) {
                proxyReq.setHeader("Authorization", `Bearer ${token}`);
              }
            });
          },
        },
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            "react-vendor": [
              "react",
              "react-dom",
              "react-router",
              "react-redux",
              "@reduxjs/toolkit",
            ],
            "ui-vendor": [
              "@radix-ui/react-avatar",
              "@radix-ui/react-label",
              "@radix-ui/react-popover",
              "@radix-ui/react-scroll-area",
              "@radix-ui/react-slot",
              "@radix-ui/react-switch",
              "@radix-ui/react-tabs",
              "@radix-ui/react-toggle",
              "lucide-react",
              "sonner",
              "class-variance-authority",
              "clsx",
              "tailwind-merge",
            ],
          },
        },
      },
    },
    // Optional: If you use process.env in client-side code, define it here:
    // define: {
    //   'process.env.VITE_BASE_WS_URL': JSON.stringify(baseWsUrl),
    // },
  };
});
