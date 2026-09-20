# Firefox Setup

Automation is now **Firefox-first**.

## Goal

Reuse your existing Firefox login sessions (LinkedIn, ATS portals) to avoid repeated login/MFA/CAPTCHA prompts.

## Recommended path

1. Start the app:

   ```bash
   pnpm dev
   ```

2. Open `http://127.0.0.1:3000/settings/browser`.
3. In **System Firefox Profiles**, pick your active daily Firefox profile.
4. Click **Use profile** (or clone it first, then use the managed clone).

## Profile source behavior

- `system`: uses your installed Firefox profile directly.
- `managed`: uses profile directories in `data/browser_profiles`.

If the system profile is locked by a running Firefox instance and `clone_system_profile_on_lock` is enabled, the app clones it into managed storage automatically.

## Config reference

`config/preferences.yaml`:

```yaml
browser:
  engine: firefox
  persistent_profile: true
  profile_source: system # or managed
  firefox_profile: default-release # when using system source
  profile: default # when using managed source
  headless: false
  reuse_existing_session: true
  clone_system_profile_on_lock: true
```

## CLI profile operations

- List profiles:
  - `python -m app.cli.main browser-profiles`
- Clone system profile:
  - `python -m app.cli.main browser-clone "<system-profile-name>" --target-name my-managed`
- Activate profile:
  - `python -m app.cli.main browser-activate my-managed --source managed`
