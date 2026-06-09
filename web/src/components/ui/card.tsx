import * as React from "react"
import { cn } from "@/lib/utils"

const ShadcnCard = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border border-border/50 bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
ShadcnCard.displayName = "ShadcnCard"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col gap-1 p-4 sm:p-5 md:p-6 pb-3", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-sm font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-xs text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-4 sm:p-5 md:p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-4 sm:p-5 md:p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

function Card({ title, description, children, className, ...props }: {
  title?: string
  description?: string
  children: React.ReactNode
  className?: string
  [key: string]: any
}) {
  if (!title) {
    return (
      <ShadcnCard className={className} {...props}>
        {children}
      </ShadcnCard>
    )
  }

  return (
    <ShadcnCard className={className} {...props}>
      <CardHeader className="pb-3">
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </ShadcnCard>
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
    <ShadcnCard className="overflow-hidden">
      <div className="p-4 sm:p-5 md:p-6 flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] sm:text-xs text-muted-foreground font-medium uppercase tracking-wider">{label}</span>
          {icon}
        </div>
        <span className="text-2xl sm:text-3xl font-bold tracking-tight">{value}</span>
        {(subtitle || trend) && (
          <div className="flex items-center gap-2 mt-0.5">
            {trend && (
              <span className={cn(
                "text-[10px] font-semibold px-1.5 py-0.5 rounded-md border",
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
    </ShadcnCard>
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
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded-md text-[10px] sm:text-[11px] font-semibold border", colors[variant])}>
      {label}
    </span>
  )
}

export {
  ShadcnCard,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  Card,
  StatCard,
  Badge,
}

