import Link from "next/link";
import { AuthCard } from "@/components/shared/AuthCard";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

export const metadata = {
  title: "Create your account — BookSphere AI",
};

export default function RegisterPage() {
  return (
    <AuthCard
      title="Create your account"
      description="Sets up your organization and gives you owner access."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <RegisterForm />
    </AuthCard>
  );
}
