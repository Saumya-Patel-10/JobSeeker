import { frontendRunCommand, resolvePython, runCommand, section, success } from "./common.mjs";

async function lint() {
  const py = resolvePython();
  section("Backend lint (ruff)");
  await runCommand(py, ["-m", "ruff", "check", "app", "tests"]);

  section("Frontend lint");
  const frontendLint = frontendRunCommand("lint");
  await runCommand(frontendLint.command, frontendLint.args);

  success("Lint checks complete.");
}

lint().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
