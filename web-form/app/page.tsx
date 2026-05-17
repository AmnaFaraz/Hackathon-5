import type { Metadata } from "next";
import SupportForm from "@/components/SupportForm";

export const metadata: Metadata = {
  title: "CloudFlow Support Portal",
  description: "AI-powered 24/7 customer support — CloudFlow by TechCorp",
};

export default function Home() {
  // API URL must be configured in Vercel environment variables.
  // See web-form/.env.example for setup instructions.
  const apiEndpoint = process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/support/submit`
    : "http://localhost:8000/support/submit";

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <SupportForm apiEndpoint={apiEndpoint} />
    </main>
  );
}
