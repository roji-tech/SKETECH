"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function SignupSuccessPage() {
  const router = useRouter();

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4">
      <div className="w-full max-w-md bg-white p-8 rounded-lg shadow-md text-center">
        <div className="flex justify-center mb-6">
          <div className="bg-green-100 p-3 rounded-full">
            <CheckCircle2 className="h-12 w-12 text-green-600" />
          </div>
        </div>

        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          Registration Successful!
        </h1>

        <p className="text-gray-600 mb-8">
          Thank you for registering with SKE TECH. Your account has been created
          successfully. Please check your email to verify your account and
          complete the setup process.
        </p>

        <div className="space-y-4">
          <Button
            onClick={() => router.push("/login")}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            Go to Login
          </Button>

          <div className="text-sm text-gray-500">
            Didn't receive an email?{" "}
            <button
              onClick={() => {
                // TODO: Implement resend verification email
                alert(
                  "Resend verification email functionality will be implemented here"
                );
              }}
              className="text-blue-600 hover:underline"
            >
              Resend verification email
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// This page will be accessible at /signup-success
