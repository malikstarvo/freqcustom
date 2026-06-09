import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-[80vh] text-center space-y-4">
      <span className="text-8xl font-bold text-[--color-card-border]">404</span>
      <h1 className="text-2xl font-bold">Page Not Found</h1>
      <p className="text-[--color-text-secondary] max-w-md">
        The page you are looking for doesn't exist or has been moved.
      </p>
      <Link
        href="/dashboard"
        className="px-6 py-2 bg-[--color-accent] hover:bg-[--color-accent-hover] text-[#0f1119] rounded-lg font-semibold text-sm"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
