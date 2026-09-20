"""Jinja2 prompt loader and registry.

Templates live in ``app/prompts/*.j2`` and are registered in
``config/prompts.yaml``. Calling code looks up entries by their logical name
("job_match", "resume_tailor", ...) — never by template filename.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.config.paths import PROMPTS_DIR
from app.config.schema import PromptEntry, PromptsConfig


class PromptRegistry:
    def __init__(
        self,
        config: PromptsConfig,
        *,
        template_dir: Path | None = None,
    ) -> None:
        self.config = config
        directory = template_dir or PROMPTS_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(directory)),
            autoescape=select_autoescape(disabled_extensions=("j2",)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def get_entry(self, name: str) -> PromptEntry:
        if name not in self.config.prompts:
            raise KeyError(f"Prompt '{name}' is not registered in config/prompts.yaml")
        return self.config.prompts[name]

    def render(self, name: str, **context: Any) -> str:
        entry = self.get_entry(name)
        template = self.env.get_template(entry.template)
        return template.render(**context)

    def has(self, name: str) -> bool:
        return name in self.config.prompts
