import { existsSync } from "node:fs";
import path from "node:path";

import { installDependencies } from "./install.mjs";
import {
  frontendRunCommand,
  frontendDir,
  resolvePython,
  rootDir,
  runCommand,
  section,
  spawnProcess,
  success,
  waitForUrl,
  warn,
} from "./common.mjs";

const backendUrl = "http://127.0.0.1:8000/status";
const frontendUrl = "http://127.0.0.1:3000";

async function ensureRuntimeReady() {
  const venvExists = existsSync(path.join(rootDir, ".venv"));
  const frontendNodeModules = existsSync(path.join(frontendDir, "node_modules"));
  if (!venvExists || !frontendNodeModules) {
    warn("Dependencies not fully installed. Running install workflow first.");
    await installDependencies();
  }

  const py = resolvePython();
  section("Preparing runtime");
  await runCommand(py, ["-m", "playwright", "install", "firefox"]);
  await runCommand(py, ["-m", "app.cli.main", "init"]);
  await runCommand(py, ["-m", "app.runtime.validator"], { allowFailure: true });
}

async function startDev() {
  await ensureRuntimeReady();

  section("Starting backend + frontend");
  const py = resolvePython();
  const backendArgs = [
    "-m",
    "uvicorn",
    "app.api.main:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
  ];
  // uvicorn --reload on Windows uses an event loop without asyncio subprocess support
  // (breaks Playwright). Hot reload is enabled on macOS/Linux only.
  if (process.platform !== "win32") {
    backendArgs.push("--reload");
  } else {
    warn("Windows: backend hot reload disabled so Playwright automation works.");
  }
  const backend = spawnProcess(py, backendArgs);
  const frontend = (() => {
  const { command, args } = frontendRunCommand("dev");
  return spawnProcess(command, args);
})();

  let shuttingDown = false;
  const children = [backend, frontend];

  const shutdown = (reason) => {
    if (shuttingDown) return;
    shuttingDown = true;
    warn(`Shutting down (${reason})...`);
    for (const child of children) {
      if (child.killed) continue;
      child.kill("SIGINT");
    }
    setTimeout(() => {
      for (const child of children) {
        if (child.killed) continue;
        child.kill("SIGTERM");
      }
    }, 2_500);
    setTimeout(() => process.exit(0), 4_500);
  };

  process.on("SIGINT", () => shutdown("SIGINT"));
  process.on("SIGTERM", () => shutdown("SIGTERM"));

  for (const child of children) {
    child.on("exit", (code) => {
      if (shuttingDown) {
        return;
      }
      warn(`A dev process exited unexpectedly with code ${code ?? "unknown"}.`);
      shutdown("child exit");
    });
  }

  section("Waiting for health checks");
  const [backendReady, frontendReady] = await Promise.all([
    waitForUrl(backendUrl, { timeoutMs: 90_000 }),
    waitForUrl(frontendUrl, { timeoutMs: 90_000 }),
  ]);

  console.log("");
  console.log("Local platform URLs");
  console.log(`- Frontend: ${frontendUrl}`);
  console.log(`- Backend:  http://127.0.0.1:8000`);
  console.log(`- API docs: http://127.0.0.1:8000/docs`);
  console.log("");
  success(`Frontend health: ${frontendReady ? "ok" : "not ready yet"}`);
  success(`Backend health: ${backendReady ? "ok" : "not ready yet"}`);
  if (!backendReady || !frontendReady) {
    warn("One or more services did not pass health checks within timeout.");
  }
  console.log("");
  console.log("Press Ctrl+C to stop all services.");
}

startDev().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
