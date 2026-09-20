import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  commandExists,
  pythonVenvPath,
  resolvePython,
  rootDir,
  runCommand,
  section,
  success,
} from "./common.mjs";

function basePython() {
  if (commandExists("python")) {
    return "python";
  }
  if (commandExists("python3")) {
    return "python3";
  }
  if (commandExists("py")) {
    return "py";
  }
  return "python3";
}

export async function installDependencies() {
  section("Validating prerequisites");
  if (!commandExists("node")) {
    throw new Error("Node.js is not installed. Install Node 20+ and retry.");
  }
  if (!commandExists("python") && !commandExists("python3")) {
    throw new Error("Python 3.12+ is not installed. Install Python and retry.");
  }

  if (!existsSync(path.join(rootDir, ".venv"))) {
    section("Creating Python virtual environment");
    await runCommand(basePython(), ["-m", "venv", pythonVenvPath()]);
  }

  const py = resolvePython();
  section("Installing backend dependencies");
  await runCommand(py, ["-m", "pip", "install", "--upgrade", "pip"]);
  await runCommand(py, ["-m", "pip", "install", "-e", ".[dev]"]);

  section("Installing frontend dependencies");
  await runCommand(process.platform === "win32" ? "npm.cmd" : "npm", ["--prefix", "frontend", "install"], {
    cwd: rootDir,
  });
  success("Dependencies installed.");
}

if (fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  installDependencies().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}
