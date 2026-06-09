import * as React from "react"
import { cn } from "@/lib/utils"
import { BoxIcon } from "lucide-react"

function Empty({
  className,
  icon: Icon = BoxIcon,
  title,
  description,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  icon?: React.ElementType
  title?: string
  description?: string
}) {
  return (
    <div
      data-slot="empty"
      className={cn(
        "flex flex-col items-center justify-center py-12 text-center",
        className
      )}
      {...props}
    >
      <Icon className="size-8 text-muted-foreground/50 mb-3" aria-hidden="true" />
      {title && (
        <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      )}
      {description && (
        <p className="text-xs text-muted-foreground/70 mt-1 max-w-xs">{description}</p>
      )}
      {children}
    </div>
  )
}

export { Empty }
