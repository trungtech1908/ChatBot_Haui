export function EmptyState({ message }: { message: string }) {
  return (
    <div className="card flex min-h-40 items-center justify-center px-6 py-10 text-center text-muted">
      {message}
    </div>
  )
}
