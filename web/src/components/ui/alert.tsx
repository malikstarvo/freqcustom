import * as React from "react"
import { cn } from "@/lib/utils"
import { AlertTriangleIcon, CheckCircleIcon, InfoIcon, XCircleIcon } from "lucide-react"

const alertVariants = {
  default: "bg-muted/50 text-foreground border-border",
  destructive: "bg-destructive/10 text-destructive border-destructive/25",
  success: "bg-profit/10 text-profit border-profit/25",
  warning: "bg-warning/10 text-warning border-warning/25",
  info: "bg-primary/10 text-primary border-primary/25",
}

const alertIcons = {
  default: InfoIcon,
  destructive: XCircleIcon,
  success: CheckCircleIcon,
  warning: AlertTriangleIcon,
  info: InfoIcon,
}

function Alert({
  className,
  variant = "default",
  children,
  ...props
}: React.ComponentProps<"div"> & {
  variant?: keyof typeof alertVariants
}) {
  const Icon = alertIcons[variant]
  return (
    <div
      data-slot="alert"
      className={cn(
        "flex items-start gap-3 rounded-lg border p-4 text-sm",
        alertVariants[variant],
        className
      )}
      {...props}
    >
      <Icon className="size-4 shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">{children}</div>
    </div>
  )
}

function AlertTitle({ className, ...props }: React.ComponentProps<"h5">) {
  return (
    <h5
      data-slot="alert-title"
      className={cn("font-medium leading-none tracking-tight mb-1", className)}
      {...props}
    />
  )
}

function AlertDescription({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="alert-description"
      className={cn("text-sm opacity-90", className)}
      {...props}
    />
  )
}

export { Alert, AlertTitle, AlertDescription }
