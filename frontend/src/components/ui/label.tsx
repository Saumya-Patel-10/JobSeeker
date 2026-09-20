import * as React from "react"

import { cn } from "@/lib/utils"

const Label = React.forwardRef<
  HTMLLabelElement,
  React.ComponentPropsWithoutRef<"label">
>(({ className, ...props }, ref) => (
  <label
    ref={ref}
    data-slot="label"
    className={cn("text-sm font-medium leading-none", className)}
    {...props}
  />
))
Label.displayName = "Label"

export { Label }
