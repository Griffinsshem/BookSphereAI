import Link from "next/link";
import { AuthCard } from "@/components/shared/AuthCard";
import { LoginForm } from "@/features/auth/components/LoginForm";

export const metadata = {
  title: "Log in — BookSphere AI",
};

export default function LoginPage() {
  return (
    <AuthCard
      title="Log in"
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-medium text-primary hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <LoginForm />
    </AuthCard>
  );
}
