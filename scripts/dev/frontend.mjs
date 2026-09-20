import { frontendRunCommand, runCommand, section } from "./common.mjs";

async function runFrontend() {
  section("Starting frontend on http://127.0.0.1:3000");
  const { command, args } = frontendRunCommand("dev", [
    "--hostname",
    "127.0.0.1",
    "--port",
    "3000",
  ]);
  await runCommand(command, args);
}

runFrontend().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
