import SupportForm from "@/components/SupportForm";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-xl w-full">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">
          CloudFlow Support Portal
        </h1>
        <SupportForm apiEndpoint={process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/support/submit` : "http://localhost:8000/support/submit"} />
      </div>
    </main>
  );
}
