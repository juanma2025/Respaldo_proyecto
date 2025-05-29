import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),  tailwindcss(),],

  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/setupTests.js",
    coverage: {
      provider: 'v8',
      reporter: ["text", "html"],
      statements: 80,
      functions: 80,
      lines: 80,
      },
      checkCoverage: true,
    },
    resolve:{
      alias: {
        src: "/src",
      },
      extensions: [".js", ".jsx", ".ts", ".tsx"],
    }

  });

    

