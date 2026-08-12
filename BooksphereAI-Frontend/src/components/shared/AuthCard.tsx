/**
 * Shared visual wrapper for every (auth) page (login, register, and
 * eventually invite-accept). Centralizing this means the logo mark,
 * card shadow, and centering treatment can never drift out of sync
 * between pages the way two independently-styled pages inevitably
 * would.
 */
export function AuthCard({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex justify-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-lg font-bold text-primary-foreground">
            B
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h1 className="mb-1 text-xl font-semibold">{title}</h1>
          {description && (
            <p className="mb-6 text-sm text-muted-foreground">{description}</p>
          )}
          {!description && <div className="mb-6" />}
          {children}
        </div>

        {footer && (
          <p className="mt-6 text-center text-sm text-muted-foreground">{footer}</p>
        )}
      </div>
    </main>
  );
}
