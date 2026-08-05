import Link from "next/link";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

export const metadata = {
  title: "Create your account — BookSphere AI",
};

export default function RegisterPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <h1 className="mb-1 text-2xl font-semibold">Create your account</h1>
      <p className="mb-6 text-sm text-gray-600">
        Sets up your organization and gives you owner access.
      </p>
      <RegisterForm />
      <p className="mt-4 text-center text-sm text-gray-600">
        Already have an account?{" "}
        <Link href="/login" className="underline">
          Log in
        </Link>
      </p>
    </main>
  );
}
