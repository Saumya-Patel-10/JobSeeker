import { resolvePython, runCommand, section } from "./common.mjs";

async function runBackend() {
  section("Starting backend API on http://127.0.0.1:8000");
  const py = resolvePython();
  await runCommand(py, [
    "-m",
    "uvicorn",
    "app.api.main:app",
    "--reload",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
  ]);
}

runBackend().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
