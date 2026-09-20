import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const rootDir = path.resolve(__dirname, "..", "..");
export const frontendDir = path.join(rootDir, "frontend");
export const isWindows = process.platform === "win32";

export function style(text, color = "36") {
  return `\u001b[${color}m${text}\u001b[0m`;
}

export function section(title) {
  console.log(`\n${style(`==> ${title}`, "36")}`);
}

export function success(text) {
  console.log(style(text, "32"));
}

export function warn(text) {
  console.log(style(text, "33"));
}

export function fail(text) {
  console.error(style(text, "31"));
}

function bin(name) {
  if (!isWindows) {
    return name;
  }
  if (name.endsWith(".exe") || name.endsWith(".cmd") || name.endsWith(".bat")) {
    return name;
  }
  if (name === "npm" || name === "pnpm") {
    return `${name}.cmd`;
  }
  return name;
}

export function commandExists(name) {
  const result = spawnSync(bin(name), ["--version"], {
    stdio: "ignore",
    cwd: rootDir,
  });
  return result.status === 0;
}

export function detectPackageManager() {
  const userAgent = process.env.npm_config_user_agent ?? "";
  if (userAgent.startsWith("pnpm/")) {
    return "pnpm";
  }
  if (commandExists("pnpm")) {
    return "pnpm";
  }
  return "npm";
}

export function resolvePython() {
  const venvPython = isWindows
    ? path.join(rootDir, ".venv", "Scripts", "python.exe")
    : path.join(rootDir, ".venv", "bin", "python");
  if (existsSync(venvPython)) {
    return venvPython;
  }
  if (commandExists("python")) {
    return "python";
  }
  return "python3";
}

export function pythonVenvPath() {
  return path.join(rootDir, ".venv");
}

export function runCommand(command, args, options = {}) {
  const { cwd = rootDir, env = process.env, allowFailure = false } = options;
  const useShell = isWindows && (command.endsWith(".cmd") || command.endsWith(".bat"));
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      env,
      stdio: "inherit",
      shell: useShell,
    });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0 || allowFailure) {
        resolve(code ?? 0);
        return;
      }
      reject(new Error(`Command failed: ${command} ${args.join(" ")} (exit ${code})`));
    });
  });
}

export function spawnProcess(command, args, options = {}) {
  const { cwd = rootDir, env = process.env } = options;
  const useShell = isWindows && (command.endsWith(".cmd") || command.endsWith(".bat"));
  return spawn(command, args, {
    cwd,
    env,
    stdio: "inherit",
    shell: useShell,
  });
}

export async function waitForUrl(url, options = {}) {
  const timeoutMs = options.timeoutMs ?? 60_000;
  const intervalMs = options.intervalMs ?? 1500;
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return true;
      }
    } catch {
      // Keep waiting.
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  return false;
}

export function frontendRunCommand(script, extraArgs = []) {
  return {
    command: bin("npm"),
    args: ["--prefix", "frontend", "run", script, ...extraArgs],
  };
}
