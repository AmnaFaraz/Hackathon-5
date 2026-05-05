"use client";

import React, { useState } from "react";

const CATEGORIES = [
  { value: "general", label: "General Question" },
  { value: "technical", label: "Technical Support" },
  { value: "billing", label: "Billing Inquiry" },
  { value: "bug_report", label: "Bug Report" },
  { value: "feedback", label: "Feedback" },
];

const PRIORITIES = [
  { value: "low", label: "Low — Not urgent" },
  { value: "medium", label: "Medium — Need help soon" },
  { value: "high", label: "High — Urgent issue" },
];

const MAX_MESSAGE_LENGTH = 1000;

type Status = "idle" | "submitting" | "success" | "error";

interface FormData {
  name: string;
  email: string;
  subject: string;
  category: string;
  priority: string;
  message: string;
}

export default function SupportForm({
  apiEndpoint = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/support/submit",
}: {
  apiEndpoint?: string;
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
  const [errors, setErrors] = useState<Partial<FormData>>({});

  const charsRemaining = MAX_MESSAGE_LENGTH - formData.message.length;
  const isOverLimit = charsRemaining < 0;

  const validate = (): boolean => {
    const newErrors: Partial<FormData> = {};

    if (!formData.name.trim() || formData.name.trim().length < 2)
      newErrors.name = "Name must be at least 2 characters.";

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email))
      newErrors.email = "Please enter a valid email address.";

    if (!formData.subject.trim() || formData.subject.trim().length < 5)
      newErrors.subject = "Subject must be at least 5 characters.";

    if (!formData.message.trim() || formData.message.trim().length < 10)
      newErrors.message = "Please describe your issue in more detail.";

    if (isOverLimit)
      newErrors.message = `Message is ${Math.abs(charsRemaining)} characters over the limit.`;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormData]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setStatus("submitting");

    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      setTicketId(data.ticket_id);
      setStatus("success");
    } catch (err) {
      setStatus("error");
    }
  };

  /* ── SUCCESS STATE ─────────────────────────────────────── */
  if (status === "success") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
        <div className="w-full max-w-lg bg-white rounded-2xl shadow-lg p-10 text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-10 h-10 text-green-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Request Submitted!
          </h2>
          <p className="text-gray-500 mb-6">
            Our AI support agent will respond to your email shortly.
          </p>

          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
            <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">
              Your Ticket ID
            </p>
            <p className="text-lg font-mono font-semibold text-blue-600">
              {ticketId}
            </p>
          </div>

          <div className="flex items-center justify-center gap-2 text-sm text-gray-400 mb-8">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            AI Agent is processing your request
          </div>

          <button
            onClick={() => {
              setStatus("idle");
              setTicketId(null);
              setFormData({
                name: "",
                email: "",
                subject: "",
                category: "general",
                priority: "medium",
                message: "",
              });
              setErrors({});
            }}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 
                       text-white font-medium rounded-xl transition-colors duration-200"
          >
            Submit Another Request
          </button>
        </div>
      </div>
    );
  }

  /* ── MAIN FORM ─────────────────────────────────────────── */
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-lg overflow-hidden">

        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 
                     9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 
                     11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">CloudFlow Support</h1>
              <p className="text-blue-100 text-sm">AI-powered · 24/7 · Instant response</p>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {status === "error" && (
          <div className="mx-8 mt-6 p-4 bg-red-50 border border-red-200 
                          rounded-xl flex items-start gap-3">
            <svg className="w-5 h-5 text-red-500 mt-0.5 shrink-0" fill="none"
              stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm font-semibold text-red-700">
                Submission failed
              </p>
              <p className="text-sm text-red-600 mt-0.5">
                Something went wrong on our end. Please try again in a moment.
                If this keeps happening, email us directly at support@cloudflow.ai
              </p>
            </div>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-8 space-y-5" noValidate>

          {/* Name + Email */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Amna Faraz"
                className={`w-full px-4 py-2.5 rounded-xl border text-sm
                  transition-colors duration-150 outline-none
                  focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  ${errors.name
                    ? "border-red-400 bg-red-50"
                    : "border-gray-200 bg-gray-50 hover:border-gray-300"
                  }`}
              />
              {errors.name && (
                <p className="mt-1 text-xs text-red-500">{errors.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Email Address <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="amna@example.com"
                className={`w-full px-4 py-2.5 rounded-xl border text-sm
                  transition-colors duration-150 outline-none
                  focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  ${errors.email
                    ? "border-red-400 bg-red-50"
                    : "border-gray-200 bg-gray-50 hover:border-gray-300"
                  }`}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-500">{errors.email}</p>
              )}
            </div>
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Subject <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              placeholder="Brief description of your issue"
              className={`w-full px-4 py-2.5 rounded-xl border text-sm
                transition-colors duration-150 outline-none
                focus:ring-2 focus:ring-blue-500 focus:border-transparent
                ${errors.subject
                  ? "border-red-400 bg-red-50"
                  : "border-gray-200 bg-gray-50 hover:border-gray-300"
                }`}
            />
            {errors.subject && (
              <p className="mt-1 text-xs text-red-500">{errors.subject}</p>
            )}
          </div>

          {/* Category + Priority */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Category <span className="text-red-500">*</span>
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 
                           bg-gray-50 text-sm outline-none
                           focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           hover:border-gray-300 transition-colors duration-150"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Priority
              </label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleChange}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200
                           bg-gray-50 text-sm outline-none
                           focus:ring-2 focus:ring-blue-500 focus:border-transparent
                           hover:border-gray-300 transition-colors duration-150"
              >
                {PRIORITIES.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Message + Character Counter */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-sm font-medium text-gray-700">
                How can we help? <span className="text-red-500">*</span>
              </label>
              <span className={`text-xs font-mono tabular-nums ${
                isOverLimit
                  ? "text-red-500 font-semibold"
                  : charsRemaining <= 100
                  ? "text-amber-500"
                  : "text-gray-400"
              }`}>
                {isOverLimit ? `${Math.abs(charsRemaining)} over limit` : `${charsRemaining} remaining`}
              </span>
            </div>
            <textarea
              name="message"
              value={formData.message}
              onChange={handleChange}
              rows={6}
              placeholder="Please describe your issue or question in detail. Include any error messages, steps to reproduce, or relevant context..."
              className={`w-full px-4 py-3 rounded-xl border text-sm resize-none
                transition-colors duration-150 outline-none
                focus:ring-2 focus:ring-blue-500 focus:border-transparent
                ${errors.message || isOverLimit
                  ? "border-red-400 bg-red-50"
                  : "border-gray-200 bg-gray-50 hover:border-gray-300"
                }`}
            />
            {errors.message && (
              <p className="mt-1 text-xs text-red-500">{errors.message}</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={status === "submitting" || isOverLimit}
            className={`w-full py-3 px-4 rounded-xl font-medium text-white
              transition-all duration-200 flex items-center justify-center gap-2
              ${status === "submitting" || isOverLimit
                ? "bg-gray-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 active:scale-[0.99] shadow-sm hover:shadow-md"
              }`}
          >
            {status === "submitting" ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10"
                    stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Submitting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Submit Support Request
              </>
            )}
          </button>

          {/* Footer note */}
          <p className="text-center text-xs text-gray-400 pt-1">
            By submitting, you agree to be contacted by our AI support team.
            All conversations are handled securely and confidentially.
          </p>
        </form>
      </div>
    </div>
  );
}
