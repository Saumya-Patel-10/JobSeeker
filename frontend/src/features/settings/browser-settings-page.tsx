"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { StatusPill } from "@/components/workflow/status-pill";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import {
  useBrowserHealth,
  useBrowserProfiles,
  useCloneBrowserProfile,
  useSetActiveBrowserProfile,
} from "@/hooks/use-console-queries";

export function BrowserSettingsPage() {
  const profiles = useBrowserProfiles();
  const health = useBrowserHealth();
  const activate = useSetActiveBrowserProfile();
  const cloneProfile = useCloneBrowserProfile();
  const [persistentProfile, setPersistentProfile] = useState(true);
  const [reuseSession, setReuseSession] = useState(true);
  const [cloneOnLock, setCloneOnLock] = useState(true);
  const [targetName, setTargetName] = useState("");

  const grouped = useMemo(() => {
    const rows = profiles.data ?? [];
    return {
      system: rows.filter((row) => row.source === "system"),
      managed: rows.filter((row) => row.source === "managed"),
    };
  }, [profiles.data]);

  async function onActivate(profileName: string, source: "system" | "managed") {
    await activate.mutateAsync({
      profile_source: source,
      profile_name: profileName,
      persistent_profile: persistentProfile,
      reuse_existing_session: reuseSession,
      clone_system_profile_on_lock: cloneOnLock,
    });
    toast.success(`Activated ${profileName} (${source})`);
  }

  async function onClone(systemProfileName: string) {
    const target = targetName.trim() || `${systemProfileName}-managed`;
    await cloneProfile.mutateAsync({
      source_profile_name: systemProfileName,
      target_name: target,
      overwrite: false,
    });
    toast.success(`Cloned profile to ${target}`);
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Browser Session Settings"
        description="Firefox-first profile management for persistent ATS login reuse."
      />

      <section className="data-grid">
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Engine
            </CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {health.data?.engine ?? "firefox"}
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Active Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <p className="text-base font-semibold">
              {health.data?.active_profile_name ?? "none"}
            </p>
            <p className="text-xs text-muted-foreground">
              {health.data?.profile_source ?? "managed"}
            </p>
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Profile Health
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <StatusPill status={health.data?.profile_exists ? "open" : "closed"} />
            <p className="text-xs text-muted-foreground">
              cookies: {health.data?.cookies_available ? "available" : "missing"}
            </p>
            <p className="text-xs text-muted-foreground">
              locked: {health.data?.locked ? "yes" : "no"}
            </p>
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Discovered Profiles
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p>system: {health.data?.detected_system_profiles ?? 0}</p>
            <p>managed: {health.data?.detected_managed_profiles ?? 0}</p>
          </CardContent>
        </Card>
      </section>

      <Card className="panel">
        <CardHeader>
          <CardTitle className="text-sm">Session Behavior</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <label className="flex items-center gap-2 text-sm">
            <Switch checked={persistentProfile} onCheckedChange={setPersistentProfile} />
            persistent profile
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Switch checked={reuseSession} onCheckedChange={setReuseSession} />
            reuse existing session cookies
          </label>
          <label className="flex items-center gap-2 text-sm">
            <Switch checked={cloneOnLock} onCheckedChange={setCloneOnLock} />
            clone system profile when locked
          </label>
        </CardContent>
      </Card>

      <section className="grid gap-4 xl:grid-cols-2">
        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">System Firefox Profiles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2">
              <Input
                placeholder="Managed clone name"
                value={targetName}
                onChange={(event) => setTargetName(event.target.value)}
              />
            </div>
            {grouped.system.map((profile) => (
              <div key={`${profile.source}:${profile.name}`} className="rounded-xl border border-border/70 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{profile.name}</p>
                  <div className="flex items-center gap-2">
                    {profile.is_default ? <Badge variant="secondary">default</Badge> : null}
                    <Badge variant="outline">system</Badge>
                  </div>
                </div>
                <p className="mt-1 truncate text-xs text-muted-foreground">{profile.path}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={() => onActivate(profile.name, "system")}
                    disabled={activate.isPending}
                  >
                    Use profile
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onClone(profile.name)}
                    disabled={cloneProfile.isPending}
                  >
                    Clone to managed
                  </Button>
                </div>
              </div>
            ))}
            {!grouped.system.length ? (
              <p className="rounded-lg border border-dashed border-border p-3 text-sm text-muted-foreground">
                No system Firefox profiles detected.
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Managed Automation Profiles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {grouped.managed.map((profile) => (
              <div key={`${profile.source}:${profile.name}`} className="rounded-xl border border-border/70 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-medium">{profile.name}</p>
                  <div className="flex items-center gap-2">
                    {profile.is_default ? <Badge variant="secondary">default</Badge> : null}
                    <Badge variant="outline">managed</Badge>
                  </div>
                </div>
                <p className="mt-1 truncate text-xs text-muted-foreground">{profile.path}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  cookies: {profile.has_cookies_db ? "yes" : "no"} · locked:{" "}
                  {profile.locked ? "yes" : "no"}
                </p>
                <div className="mt-2">
                  <Button
                    size="sm"
                    onClick={() => onActivate(profile.name, "managed")}
                    disabled={activate.isPending}
                  >
                    Use profile
                  </Button>
                </div>
              </div>
            ))}
            {!grouped.managed.length ? (
              <p className="rounded-lg border border-dashed border-border p-3 text-sm text-muted-foreground">
                No managed profiles yet. Clone from a system profile to seed one.
              </p>
            ) : null}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
