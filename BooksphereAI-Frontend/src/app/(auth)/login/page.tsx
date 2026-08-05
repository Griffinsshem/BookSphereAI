import Link from "next/link";
import { LoginForm } from "@/features/auth/components/LoginForm";

export const metadata = {
  title: "Log in — BookSphere AI",
};

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <h1 className="mb-6 text-2xl font-semibold">Log in</h1>
      <LoginForm />
      <p className="mt-4 text-center text-sm text-gray-600">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="underline">
          Create one
        </Link>
      </p>
    </main>
  );
}
