import * as React from "react"
import { cn } from "@/lib/utils"

function Card({ title, description, className, children, ...props }: React.ComponentProps<"div"> & {
  title?: string
  description?: string
}) {
  const cardClasses = cn(
    "rounded-xl border border-border/50 bg-card text-card-foreground shadow-sm",
    className
  )

  if (title) {
    return (
      <div data-slot="card" className={cardClasses} {...props}>
        <CardHeader className="pb-3">
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>{children}</CardContent>
      </div>
    )
  }

  return (
    <div data-slot="card" className={cardClasses} {...props}>
      {children}
    </div>
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-header"
      className={cn("flex flex-col gap-1.5 p-5 sm:p-6", className)}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<"h3">) {
  return (
    <h3
      data-slot="card-title"
      className={cn("text-base font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  )
}

function CardDescription({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      data-slot="card-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-content"
      className={cn("p-5 sm:p-6 pt-0", className)}
      {...props}
    />
  )
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-footer"
      className={cn("flex items-center p-5 sm:p-6 pt-0", className)}
      {...props}
    />
  )
}

function StatCard({ label, value, subtitle = "", trend = "", icon }: {
  label: string
  value: string | number
  subtitle?: string
  trend?: string
  icon?: React.ReactNode
}) {
  const isPositive = trend.startsWith("+")
  const isNegative = trend.startsWith("-")

  return (
    <Card className="overflow-hidden">
      <div className="p-4 sm:p-5 md:p-6 flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">
            {label}
          </span>
          {icon}
        </div>
        <span className="text-2xl sm:text-3xl font-bold tracking-tight">{value}</span>
        {(subtitle || trend) && (
          <div className="flex items-center gap-2 mt-0.5">
            {trend && (
              <span className={cn(
                "text-xs font-semibold px-2 py-0.5 rounded-md border",
                isPositive && "bg-profit/10 border-profit/20 text-profit",
                isNegative && "bg-loss/10 border-loss/20 text-loss",
                !isPositive && !isNegative && "bg-muted/50 border-border/50 text-muted-foreground"
              )}>
                {trend}
              </span>
            )}
            {subtitle && <span className="text-xs text-muted-foreground">{subtitle}</span>}
          </div>
        )}
      </div>
    </Card>
  )
}

function Badge({ label, variant = "default" }: { label: string; variant?: "default" | "success" | "danger" | "warning" | "info" }) {
  const colors = {
    default: "bg-muted/50 text-muted-foreground border-border/50",
    success: "bg-profit/10 text-profit border-profit/25",
    danger: "bg-loss/10 text-loss border-loss/25",
    warning: "bg-warning/10 text-warning border-warning/25",
    info: "bg-primary/10 text-primary border-primary/25",
  }
  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold border",
      colors[variant]
    )}>
      {label}
    </span>
  )
}

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  StatCard,
  Badge,
}
