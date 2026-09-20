import { frontendRunCommand, resolvePython, runCommand, section, success } from "./common.mjs";

async function doctor() {
  const py = resolvePython();
  section("Runtime validator");
  await runCommand(py, ["-m", "app.runtime.validator"]);

  section("Backend doctor checks");
  await runCommand(py, ["-m", "app.cli.main", "doctor"], { allowFailure: true });

  section("Frontend diagnostics");
  const typecheck = frontendRunCommand("typecheck");
  await runCommand(typecheck.command, typecheck.args);

  success("Doctor checks complete.");
}

doctor().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
