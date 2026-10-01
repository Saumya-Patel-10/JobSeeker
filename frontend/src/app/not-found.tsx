import Link from "next/link"

import { Logo } from "@/components/brand/logo"
import { buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-5 px-5 text-center">
      <Logo />
      <p className="text-sm font-medium text-primary">404</p>
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="text-sm text-muted-foreground">
        The page you are looking for does not exist or has moved.
      </p>
      <Link href="/dashboard" className={cn(buttonVariants({ variant: "default" }), "h-10 px-5")}>
        Back to dashboard
      </Link>
    </div>
  )
}
