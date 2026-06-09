import * as React from "react"
import { cn } from "@/lib/utils"

const ShadcnCard = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-all duration-300 hover:shadow-md hover:border-border/80 relative overflow-hidden group/card",
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
    className={cn("flex flex-col space-y-1.5 p-6", className)}
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
      "text-lg font-semibold leading-none tracking-tight",
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
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

// Unified legacy/new Card component
export function Card({ title, children, className = "", ...props }: {
  title?: string;
  children: React.ReactNode;
  className?: string;
  [key: string]: any;
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
      <CardHeader className="pb-3 border-b border-border/40 mb-4 bg-muted/20">
        <CardTitle className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </ShadcnCard>
  )
}

// StatCard helper component
export function StatCard({ label, value, subtitle = "", trend = "" }: {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
}) {
  const isPositive = trend.startsWith("+");
  const isNegative = trend.startsWith("-");

  return (
    <ShadcnCard className="relative overflow-hidden group hover:border-primary/50 transition-all duration-300">
      <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
      <CardContent className="p-6">
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">{label}</span>
          <span className="text-3xl font-extrabold tracking-tight">{value}</span>
          {(subtitle || trend) && (
            <div className="flex items-center gap-2 mt-1">
              {trend && (
                <span className={cn(
                  "text-[10px] font-bold px-2 py-0.5 rounded-full border",
                  isPositive && "bg-profit/10 border-profit/20 text-profit",
                  isNegative && "bg-loss/10 border-loss/20 text-loss",
                  !isPositive && !isNegative && "bg-muted border-border text-muted-foreground"
                )}>
                  {trend}
                </span>
              )}
              {subtitle && <span className="text-xs text-muted-foreground">{subtitle}</span>}
            </div>
          )}
        </div>
      </CardContent>
    </ShadcnCard>
  );
}

// Badge helper component
export function Badge({ label, variant = "default" }: { label: string; variant?: "default" | "success" | "danger" | "warning" | "info" }) {
  const colors = {
    default: "bg-muted text-muted-foreground border-border/60",
    success: "bg-profit/10 text-profit border-profit/25",
    danger: "bg-loss/10 text-loss border-loss/25",
    warning: "bg-warning/10 text-warning border-warning/25",
    info: "bg-primary/10 text-primary border-primary/25",
  };
  return (
    <span className={cn("px-2.5 py-0.5 rounded-full text-[10px] font-bold border transition-colors", colors[variant])}>
      {label}
    </span>
  );
}

export {
  ShadcnCard,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
}
