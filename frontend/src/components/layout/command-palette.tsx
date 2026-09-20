"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { navItems } from "@/components/layout/nav-config";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { useJobs } from "@/hooks/use-console-queries";
import { useUiStore } from "@/stores/ui-store";

export function CommandPalette() {
  const router = useRouter();
  const open = useUiStore((state) => state.commandOpen);
  const setOpen = useUiStore((state) => state.setCommandOpen);
  const setSelectedJobId = useUiStore((state) => state.setSelectedJobId);
  const jobsQuery = useJobs({ limit: 15 });

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setOpen(!open);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, setOpen]);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search pages, jobs, actions..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          {navItems.map((item) => (
            <CommandItem
              key={item.href}
              onSelect={() => {
                router.push(item.href);
                setOpen(false);
              }}
            >
              <item.icon className="size-4" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Recent Jobs">
          {jobsQuery.data?.map((job) => (
            <CommandItem
              key={job.id}
              onSelect={() => {
                setSelectedJobId(job.id);
                router.push(`/jobs/${job.id}`);
                setOpen(false);
              }}
            >
              <span className="font-medium">{job.title}</span>
              <span className="ml-2 text-muted-foreground">@ {job.company}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
