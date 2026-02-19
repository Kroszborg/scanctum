export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="flex min-h-screen items-center justify-center grid-bg"
      style={{ background: "#0c0a08" }}
    >
      {children}
    </div>
  );
}
