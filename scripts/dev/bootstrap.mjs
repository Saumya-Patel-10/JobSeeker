import { installDependencies } from "./install.mjs";
import { resolvePython, runCommand, section, success, warn } from "./common.mjs";

async function bootstrap() {
  section("Bootstrap started");
  await installDependencies();

  const py = resolvePython();

  section("Installing Playwright Firefox runtime");
  await runCommand(py, ["-m", "playwright", "install", "firefox"]);

  section("Initializing database and data directories");
  await runCommand(py, ["-m", "app.cli.main", "init"]);

  section("Running runtime validator");
  await runCommand(py, ["-m", "app.runtime.validator"]);

  section("Running doctor checks");
  await runCommand(py, ["-m", "app.cli.main", "doctor"], {
    allowFailure: true,
  });
  warn(
    "If LLM is offline, doctor may show WARN - start LM Studio/Ollama before running pipelines."
  );

  success("Bootstrap complete. Run `pnpm dev` (or `npm run dev`) to start the full stack.");
}

bootstrap().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
