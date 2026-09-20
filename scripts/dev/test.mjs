import { frontendRunCommand, resolvePython, runCommand, section, success } from "./common.mjs";

async function test() {
  const py = resolvePython();
  section("Backend tests");
  await runCommand(py, ["-m", "pytest", "-q"]);

  section("Frontend type checks");
  const frontendTypecheck = frontendRunCommand("typecheck");
  await runCommand(frontendTypecheck.command, frontendTypecheck.args);

  success("Test suite complete.");
}

test().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
