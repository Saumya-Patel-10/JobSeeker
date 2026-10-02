"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { History, Save } from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { useProfile, useUpdateProfile } from "@/hooks/use-console-queries"
import { formatDateTime } from "@/utils/format"

const profileFormSchema = z.object({
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().min(5),
  linkedin: z.string().optional(),
  github: z.string().optional(),
  portfolio: z.string().optional(),
  authorized_country: z.string().min(1),
  requires_sponsorship: z.boolean(),
  salary_min: z.coerce.number().int().nonnegative().optional(),
  salary_target: z.coerce.number().int().nonnegative().optional(),
  salary_max: z.coerce.number().int().nonnegative().optional(),
  skills_csv: z.string().optional(),
  standard_answers_json: z.string().optional(),
  employment_json: z.string().optional(),
})

type ProfileForm = z.infer<typeof profileFormSchema>

interface ProfileVersion {
  at: string
  payload: ProfileForm
}

const VERSION_KEY = "profile-manager-versions"

export function ProfileManagerPage() {
  const profileQuery = useProfile()
  const updateProfile = useUpdateProfile()
  const [autosave, setAutosave] = useState(true)
  const [versions, setVersions] = useState<ProfileVersion[]>([])

  const form = useForm<ProfileForm>({
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      linkedin: "",
      github: "",
      portfolio: "",
      authorized_country: "United States",
      requires_sponsorship: false,
      salary_min: undefined,
      salary_target: undefined,
      salary_max: undefined,
      skills_csv: "",
      standard_answers_json: "[]",
      employment_json: "[]",
    },
  })

  useEffect(() => {
    const raw = window.localStorage.getItem(VERSION_KEY)
    if (!raw) return
    try {
      const parsed = JSON.parse(raw) as ProfileVersion[]
      setVersions(parsed)
    } catch {
      setVersions([])
    }
  }, [])

  useEffect(() => {
    const profile = profileQuery.data
    if (!profile) return
    const personal = (profile.personal ?? {}) as Record<string, unknown>
    const links = (profile.links ?? {}) as Record<string, unknown>
    const workAuth = (profile.work_authorization ?? {}) as Record<string, unknown>
    const salary = (profile.salary ?? {}) as Record<string, unknown>
    const skills = (profile.skills ?? []) as string[]
    const standardAnswers = (profile.standard_answers ?? []) as unknown[]
    const employment = (profile.employment ?? []) as unknown[]

    const authorizedCountries = Array.isArray(workAuth.authorized_to_work_in)
      ? workAuth.authorized_to_work_in
      : []

    form.reset({
      first_name: String(personal.first_name ?? ""),
      last_name: String(personal.last_name ?? ""),
      email: String(personal.email ?? ""),
      phone: String(personal.phone ?? ""),
      linkedin: String(links.linkedin ?? ""),
      github: String(links.github ?? ""),
      portfolio: String(links.portfolio ?? ""),
      authorized_country: String(authorizedCountries[0] ?? "United States"),
      requires_sponsorship: Boolean(workAuth.requires_sponsorship),
      salary_min: Number(salary.minimum ?? 0) || undefined,
      salary_target: Number(salary.target ?? 0) || undefined,
      salary_max: Number(salary.maximum ?? 0) || undefined,
      skills_csv: skills.join(", "),
      standard_answers_json: JSON.stringify(standardAnswers, null, 2),
      employment_json: JSON.stringify(employment, null, 2),
    })
  }, [form, profileQuery.data])

  const persist = useCallback(async (values: ProfileForm) => {
    const parsedForm = profileFormSchema.safeParse(values)
    if (!parsedForm.success) {
      toast.error("Profile form validation failed")
      return
    }

    let standardAnswers: unknown[] = []
    let employment: unknown[] = []
    try {
      standardAnswers = values.standard_answers_json ? JSON.parse(values.standard_answers_json) : []
      employment = values.employment_json ? JSON.parse(values.employment_json) : []
    } catch {
      toast.error("Failed to parse JSON sections")
      return
    }

    const payload: Record<string, unknown> = {
      ...profileQuery.data,
      personal: {
        ...(profileQuery.data?.personal as Record<string, unknown> | undefined),
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        phone: values.phone,
      },
      links: {
        ...(profileQuery.data?.links as Record<string, unknown> | undefined),
        linkedin: values.linkedin || null,
        github: values.github || null,
        portfolio: values.portfolio || null,
      },
      work_authorization: {
        ...(profileQuery.data?.work_authorization as Record<string, unknown> | undefined),
        authorized_to_work_in: [values.authorized_country],
        requires_sponsorship: values.requires_sponsorship,
      },
      salary: {
        ...(profileQuery.data?.salary as Record<string, unknown> | undefined),
        minimum: values.salary_min ?? null,
        target: values.salary_target ?? null,
        maximum: values.salary_max ?? null,
      },
      skills: values.skills_csv
        ? values.skills_csv
            .split(",")
            .map((skill) => skill.trim())
            .filter(Boolean)
        : [],
      standard_answers: standardAnswers,
      employment,
    }

    await updateProfile.mutateAsync(payload)
    toast.success("Profile saved")

    const snapshot: ProfileVersion = {
      at: new Date().toISOString(),
      payload: values,
    }
    const updated = [snapshot, ...versions].slice(0, 15)
    setVersions(updated)
    window.localStorage.setItem(VERSION_KEY, JSON.stringify(updated))
  }, [profileQuery.data, updateProfile, versions])

  const watched = form.watch()
  useEffect(() => {
    if (!autosave || !form.formState.isDirty) return
    const handle = window.setTimeout(() => {
      void form.handleSubmit(persist)()
    }, 1600)
    return () => window.clearTimeout(handle)
  }, [autosave, form, persist, watched])

  const restoreVersion = (version: ProfileVersion) => {
    form.reset(version.payload)
    toast.message(`Loaded snapshot from ${formatDateTime(version.at)}`)
  }

  const standardAnswersText = form.watch("standard_answers_json") || "[]"
  const employmentText = form.watch("employment_json") || "[]"
  const hasJsonError = useMemo(() => {
    try {
      JSON.parse(standardAnswersText)
      JSON.parse(employmentText)
      return false
    } catch {
      return true
    }
  }, [employmentText, standardAnswersText])

  return (
    <div className="space-y-4">
      <PageHeader
        title="Profile Manager"
        description="Editable profile form with autosave, validation, and local version snapshots."
      />
      <div className="grid gap-4 xl:grid-cols-[1fr,320px]">
        <Card className="rounded-2xl border-border/70 bg-card/50">
          <CardHeader>
            <CardTitle className="text-sm">Candidate Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="grid gap-4 sm:grid-cols-2"
              onSubmit={form.handleSubmit(persist)}
            >
              <div className="space-y-2">
                <Label>First name</Label>
                <Input {...form.register("first_name")} />
              </div>
              <div className="space-y-2">
                <Label>Last name</Label>
                <Input {...form.register("last_name")} />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input {...form.register("email")} />
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input {...form.register("phone")} />
              </div>
              <div className="space-y-2">
                <Label>LinkedIn</Label>
                <Input {...form.register("linkedin")} placeholder="https://linkedin.com/in/yourname" />
              </div>
              <div className="space-y-2">
                <Label>GitHub</Label>
                <Input {...form.register("github")} placeholder="https://github.com/yourname" />
              </div>
              <div className="space-y-2">
                <Label>Portfolio Website</Label>
                <Input {...form.register("portfolio")} placeholder="https://your-portfolio.netlify.app" />
              </div>
              <div className="space-y-2">
                <Label>Authorized country</Label>
                <Input {...form.register("authorized_country")} />
              </div>
              <div className="flex items-center gap-3 pt-6">
                <Switch
                  checked={form.watch("requires_sponsorship")}
                  onCheckedChange={(checked) =>
                    form.setValue("requires_sponsorship", checked, { shouldDirty: true })
                  }
                />
                <Label>Requires sponsorship</Label>
              </div>

              <div className="space-y-2">
                <Label>Salary minimum</Label>
                <Input type="number" {...form.register("salary_min")} />
              </div>
              <div className="space-y-2">
                <Label>Salary target</Label>
                <Input type="number" {...form.register("salary_target")} />
              </div>
              <div className="space-y-2">
                <Label>Salary maximum</Label>
                <Input type="number" {...form.register("salary_max")} />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Skills (comma separated)</Label>
                <Input {...form.register("skills_csv")} />
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label>Standard application answers (JSON array)</Label>
                <Textarea className="min-h-28 font-mono text-xs" {...form.register("standard_answers_json")} />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label>Employment history (JSON array)</Label>
                <Textarea className="min-h-32 font-mono text-xs" {...form.register("employment_json")} />
              </div>
              <div className="sm:col-span-2 flex items-center gap-3">
                <Button type="submit" disabled={updateProfile.isPending || hasJsonError}>
                  <Save className="mr-2 size-4" />
                  Save profile
                </Button>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Switch checked={autosave} onCheckedChange={setAutosave} />
                  Autosave
                </div>
                {hasJsonError ? (
                  <p className="text-xs text-destructive">JSON section has invalid syntax.</p>
                ) : null}
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/70 bg-card/50">
          <CardHeader>
            <CardTitle className="text-sm">
              <History className="mr-2 inline size-4" />
              Local Versions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[70vh]">
              <div className="space-y-2">
                {versions.map((version) => (
                  <button
                    type="button"
                    key={version.at}
                    onClick={() => restoreVersion(version)}
                    className="w-full rounded-lg border border-border/70 p-2 text-left hover:bg-muted/30"
                  >
                    <p className="text-xs font-medium">{formatDateTime(version.at)}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {version.payload.first_name} {version.payload.last_name}
                    </p>
                  </button>
                ))}
                {!versions.length ? (
                  <p className="rounded-lg border border-dashed border-border p-3 text-xs text-muted-foreground">
                    No snapshots saved yet.
                  </p>
                ) : null}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
