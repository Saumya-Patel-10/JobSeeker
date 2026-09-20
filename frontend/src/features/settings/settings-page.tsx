"use client"

import { useEffect } from "react"
import Link from "next/link"
import { z } from "zod"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { useSettings, useUpdateSettings } from "@/hooks/use-console-queries"
import type { SettingsSection } from "@/types/api"

const jsonSchema = z.object({
  json: z.string().min(2).refine((value) => {
    try {
      JSON.parse(value)
      return true
    } catch {
      return false
    }
  }, "Must be valid JSON"),
})

type JsonForm = z.infer<typeof jsonSchema>

function SettingsEditor({
  section,
  title,
  description,
  value,
}: {
  section: SettingsSection
  title: string
  description: string
  value: unknown
}) {
  const updateSettings = useUpdateSettings()
  const form = useForm<JsonForm>({
    resolver: zodResolver(jsonSchema),
    defaultValues: {
      json: JSON.stringify(value ?? {}, null, 2),
    },
  })

  useEffect(() => {
    form.reset({
      json: JSON.stringify(value ?? {}, null, 2),
    })
  }, [form, value])

  const onSubmit = form.handleSubmit(async (payload) => {
    const parsed = JSON.parse(payload.json) as Record<string, unknown>
    await updateSettings.mutateAsync({
      section,
      data: parsed,
    })
    toast.success(`${title} updated`)
  })

  return (
    <Card className="rounded-2xl border-border/70 bg-card/50">
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardHeader>
      <CardContent className="space-y-3">
        <form onSubmit={onSubmit} className="space-y-3">
          <Textarea
            className="min-h-[42vh] font-mono text-xs"
            value={form.watch("json")}
            onChange={(event) => form.setValue("json", event.target.value, { shouldValidate: true })}
          />
          {form.formState.errors.json ? (
            <p className="text-xs text-destructive">{form.formState.errors.json.message}</p>
          ) : null}
          <div className="flex items-center gap-2">
            <Button type="submit" disabled={updateSettings.isPending}>
              Save {title}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

export function SettingsPage() {
  const settings = useSettings()

  return (
    <div className="space-y-4">
      <PageHeader
        title="Settings & Configuration"
        description="Edit runtime configuration through structured forms; no manual YAML edits required."
        right={
          <Link href="/settings/browser">
            <Button variant="outline">Open Browser Session Manager</Button>
          </Link>
        }
      />
      <Tabs defaultValue="preferences" className="panel p-3">
        <TabsList className="flex flex-wrap">
          <TabsTrigger value="preferences">preferences.yaml</TabsTrigger>
          <TabsTrigger value="job_sources">job_sources.yaml</TabsTrigger>
          <TabsTrigger value="blacklist">blacklist.yaml</TabsTrigger>
          <TabsTrigger value="profile">profile.yaml</TabsTrigger>
        </TabsList>

        <TabsContent value="preferences" className="mt-3">
          <SettingsEditor
            section="preferences"
            title="preferences.yaml"
            description="LLM, browser automation, apply safety, and scoring weights."
            value={settings.data?.preferences}
          />
        </TabsContent>

        <TabsContent value="job_sources" className="mt-3">
          <SettingsEditor
            section="job_sources"
            title="job_sources.yaml"
            description="Configured ATS and URL sources consumed by the search pipeline."
            value={settings.data?.job_sources}
          />
        </TabsContent>

        <TabsContent value="blacklist" className="mt-3">
          <SettingsEditor
            section="blacklist"
            title="blacklist.yaml"
            description="Company/domain/keyword filters to skip low quality opportunities."
            value={settings.data?.blacklist}
          />
        </TabsContent>

        <TabsContent value="profile" className="mt-3">
          <SettingsEditor
            section="profile"
            title="profile.yaml"
            description="Raw profile document. For a guided form, use Profile Manager."
            value={settings.data?.profile}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
