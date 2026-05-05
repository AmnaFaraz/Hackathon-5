"use client";

import React, { useState } from "react";

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

interface SubmitResponse {
  ticket_id: string;
  message: string;
  estimated_response_time: string;
}

type Status = "idle" | "submitting" | "success" | "error";

const CATEGORIES = [
  { value: "general", label: "General Question" },
  { value: "technical", label: "Technical Support" },
  { value: "billing", label: "Billing Inquiry" },
  { value: "bug_report", label: "Bug Report" },
  { value: "feedback", label: "Feedback" },
];

const PRIORITIES = [
  { value: "low", label: "Low - Not urgent" },
  { value: "medium", label: "Medium - Need help soon" },
  { value: "high", label: "High - Urgent issue" },
];

export default function SupportForm({ 
  apiEndpoint = "http://localhost:8000/support/submit" 
}: { 
  apiEndpoint?: string 
}) {
  const [formData, setFormData] = useState<FormData>({
    name: "",
    email: "",
    subject: "",
    category: "general",
    priority: "medium",
    message: "",
  });

  const [status, setStatus] = useState<Status>("idle");
  const [ticketId, setTicketId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validateForm = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return (
      formData.name.length >= 2 &&
      emailRegex.test(formData.email) &&
      formData.subject.length >= 5 &&
      formData.message.length >= 10
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
      setError("Please fill all fields correctly. Name min 2 chars, message min 10.");
      return;
    }

    setStatus("submitting");
    setError(null);

    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("Submission failed");

      const data: SubmitResponse = await response.json();
      setTicketId(data.ticket_id);
      setStatus("success");
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div className="bg-white p-8 rounded-xl shadow-lg text-center animate-in fade-in zoom-in duration-300">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
          <svg className="h-10 w-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h2>
        <p className="text-gray-600 mb-6">Your request has been priority-queued for our AI agent.</p>
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Ticket Reference</p>
          <code className="text-lg font-mono text-blue-600 break-all">{ticketId}</code>
        </div>
        <button
          onClick={() => setStatus("idle")}
          className="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 transition duration-200"
        >
          Submit Another Request
        </button>
      </div>
    );
  }

  const inputClasses = "w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition";

  return (
    <div className="bg-white p-8 rounded-xl shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              className={inputClasses}
              placeholder="Your Name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              className={inputClasses}
              placeholder="name@company.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
          <input
            type="text"
            name="subject"
            required
            value={formData.subject}
            onChange={handleChange}
            className={inputClasses}
            placeholder="What do you need help with?"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              className={inputClasses}
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select
              name="priority"
              value={formData.priority}
              onChange={handleChange}
              className={inputClasses}
            >
              {PRIORITIES.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <div className="flex justify-between mb-1">
            <label className="block text-sm font-medium text-gray-700">Message</label>
            <span className={`text-xs ${formData.message.length > 1000 ? 'text-red-500' : 'text-gray-400'}`}>
              {formData.message.length}/1000
            </span>
          </div>
          <textarea
            name="message"
            rows={4}
            required
            value={formData.message}
            onChange={handleChange}
            className={`${inputClasses} resize-none`}
            placeholder="Tell us about the issue..."
          ></textarea>
        </div>

        {error && (
          <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg">{error}</p>
        )}

        <button
          type="submit"
          disabled={status === "submitting"}
          className={`w-full py-3 rounded-lg font-semibold text-white transition duration-200 flex items-center justify-center ${
            status === "submitting" ? "bg-blue-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 shadow-md"
          }`}
        >
          {status === "submitting" ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </>
          ) : (
            "Submit Request"
          )}
        </button>

        <p className="text-center text-sm text-gray-500">
          By submitting, you agree to be contacted by our AI support team.
          All conversations are handled securely and confidentially.
        </p>
      </form>
    </div>
  );
}
