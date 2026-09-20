# Adapter development guide

Adapters live under `app/ats/`. To add support for a new ATS, implement
`ATSAdapter` (`app/ats/base.py`) and register the class in
`app/ats/registry.py:SPECIFIC_ADAPTERS`.

## Contract

```python
class ATSAdapter(ABC):
    name: ClassVar[str]

    @classmethod
    @abstractmethod
    def detect(cls, url: str, html: str | None = None) -> bool: ...

    @abstractmethod
    async def scrape_job(self, url: str) -> Job: ...

    async def login(self, session: BrowserSession) -> None: ...   # default no-op
    async def dry_run(self, ctx: ApplicationContext) -> DryRunReport: ...

    @abstractmethod
    async def fill_application(self, ctx: ApplicationContext) -> FillReport: ...

    @abstractmethod
    async def submit(self, ctx: ApplicationContext) -> SubmitReport: ...
```

## Worked example: a new "Workday" adapter

1. Create `app/ats/workday.py`:

   ```python
   import re
   from app.ats.base import ATSAdapter
   from app.automation import selectors
   from app.models.application import ApplicationContext, FillReport, SubmitReport
   from app.models.enums import ATSSource
   from app.models.job import Job
   from app.utils.hashing import url_hash

   class WorkdayAdapter(ATSAdapter):
       name = "workday"
       URL = re.compile(r"https?://(?P<host>[^/]+myworkdayjobs\.com)/.*?/job/(?P<slug>[^/?]+)")

       @classmethod
       def detect(cls, url: str, html: str | None = None) -> bool:
           return "myworkdayjobs.com" in url.lower()

       async def scrape_job(self, url: str) -> Job:
           if self.session is None:
               raise ScrapeError("Workday adapter requires a browser session")
           page = await self.session.new_page()
           try:
               await page.goto(url, wait_until="networkidle")
               title = (await page.locator("[data-automation-id='jobTitle']").first.inner_text()).strip()
               company = (await page.locator("[data-automation-id='company']").first.inner_text()).strip()
               description = (await page.locator("[data-automation-id='jobPostingDescription']").first.inner_text()).strip()
               return Job(
                   title=title,
                   company=company,
                   description_text=description,
                   source_url=url,
                   ats_source=ATSSource.generic,  # extend ATSSource if you want a dedicated value
                   url_hash=url_hash(url),
               )
           finally:
               await page.close()

       async def fill_application(self, ctx: ApplicationContext) -> FillReport: ...
       async def submit(self, ctx: ApplicationContext) -> SubmitReport: ...
   ```

2. Register in `app/ats/registry.py`:

   ```python
   from app.ats.workday import WorkdayAdapter

   SPECIFIC_ADAPTERS = [GreenhouseAdapter, LeverAdapter, LinkedInAdapter, WorkdayAdapter]
   ```

3. Add a `detect` test in `tests/unit/test_adapters_detect.py`.

4. (Optional) Extend `app/models/enums.py:ATSSource` if you want a dedicated
   `workday` source value persisted on `jobs.ats_source`.

## Tips for resilient adapters

- **Use the public JSON API when one exists.** It's faster, less fragile,
  and works without Playwright. Greenhouse and Lever both have free public
  endpoints — see how `GreenhouseAdapter` and `LeverAdapter` use them.
- **Screenshot on failure.** `BrowserSession.screenshot` is one line and
  saves your future self hours of debugging.
- **Prefer `locator(...).first.fill(...)` over `page.fill`** — the locator
  API is auto-retrying and more resilient to DOM changes.
- **Don't auto-submit when the ATS doesn't expect it.** If the ATS shows a
  confirmation modal, decompose `submit` into a fill phase that ends at
  the modal, then a separate confirm phase.
- **Be honest in `detect`.** Return False when uncertain so the generic
  fallback can take over rather than crashing your adapter mid-form.

## Testing an adapter

For scrape-only adapters that hit a public JSON API, use `respx` to mock
HTTP. For Playwright-driven adapters, save a representative HTML fixture
under `tests/fixtures/` and write the adapter to accept either a live page
or a `page.set_content(...)`-style fixture.
