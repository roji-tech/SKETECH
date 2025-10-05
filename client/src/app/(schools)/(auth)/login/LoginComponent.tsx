"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, SubmitHandler } from "react-hook-form";
import Link from "next/link";
import { getActualPath, getApiUrl, setCookie } from "@/lib/utils";
import { signIn } from "next-auth/react";
import { toast } from "react-hot-toast";
import { BASE_URL } from "../../../../../config";
import axios from "axios";

interface SchoolInfo {
  id: number;
  name: string;
  address: string;
  phone: string;
  email: string;
  logo: string;
  short_name: string;
  code: string;
  website: string | null;
  motto: string;
  about: string;
}

type LoginFormInputs = {
  email: string;
  password: string;
  rememberMe?: boolean;
};

const Eye = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
    />
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
    />
  </svg>
);

const EyeOff = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
    />
  </svg>
);

export function LoginComponent() {
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();
  const [schoolInfo, setSchoolInfo] = useState<SchoolInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<LoginFormInputs>();

  const onSubmit: SubmitHandler<LoginFormInputs> = async (data) => {
    setLoading(true);
    setError(null);

    try {
      const result = await signIn("credentials", {
        email: data.email.trim(),
        password: data.password,
        redirect: false,
      });

      if (result?.error) {
        let errorMessage = "An unexpected error occurred. Please try again.";
        console.error("Login error:", result.error);

        // Handle different error cases
        if (result.error.includes("ECONNREFUSED")) {
          errorMessage =
            "Unable to connect to the server. Please check your internet connection or try again later.";
        } else if (
          result.error.includes("401") ||
          result.error.includes("Invalid email or password")
        ) {
          errorMessage =
            "Invalid email or password. Please check your credentials and try again.";
        } else if (
          result.error.includes("Invalid token") ||
          result.error.includes("token")
        ) {
          errorMessage = "Authentication error. Please log in again.";
        } else if (
          result.error.includes("timeout") ||
          result.error.includes("Network Error")
        ) {
          errorMessage =
            "Request timed out. Please check your internet connection and try again.";
        }

        setError(errorMessage);
        toast.error(errorMessage, { duration: 5000 });
        return;
      }

      // If we get here, login was successful
      toast.success("Login successful!", { duration: 3000 });

      // Store remember me preference if checked
      if (data.rememberMe) {
        localStorage.setItem("rememberMe", "true");
      } else {
        localStorage.removeItem("rememberMe");
      }

      // Redirect to dashboard after a short delay to show success message
      setTimeout(() => {
        router.push(`${getActualPath("/dashboard")}`);
      }, 1000);
    } catch (error: any) {
      console.error("Login failed:", error);
      const errorMessage =
        error?.message || "An unexpected error occurred. Please try again.";
      setError(errorMessage);
      toast.error(errorMessage, { duration: 5000 });
    } finally {
      setLoading(false);
    }
  };

  const formStyles = (hasError: boolean, otherStyles = "") =>
    `w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
      hasError
        ? "border-red-500 focus:ring-red-200"
        : "border-gray-300 focus:ring-blue-200"
    } bg-white transition duration-200 ${otherStyles}`;

  useEffect(() => {
    const fetchSchoolInfo = async () => {
      try {
        const url = `${BASE_URL}${getApiUrl("/school_info/")}`;
        const response = await axios.get<SchoolInfo>(url);
        setSchoolInfo(response.data);
      } catch (error) {
        console.error("Error fetching school info:", error);
        toast.error("Failed to load school information");
        router.push("/schools");
      }
    };

    // fetchSchoolInfo();
  }, [router]);

  // if (!schoolInfo) {
  //   return (
  //     <div className="flex items-center justify-center min-h-screen bg-gray-50">
  //       <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
  //     </div>
  //   );
  // }

  return (
    <div className="flex items-center w-[90%] max-w-[600px] justify-center min-h-[calc(100vh-160px)] bg-gradient-to-br bg-transparent">
      <div className="w-full bg-white rounded-2xl shadow-xl overflow-hidden">
        {/* School Header */}
        <div className="bg-blue-600 text-white p-6 text-center">
          <div className="flex justify-center mb-3">
            <img
              src={schoolInfo?.logo || "/logo.png"}
              alt={`${schoolInfo?.name || ""} Logo`}
              className="w-16 h-16 rounded-full border-2 border-white object-cover"
              onError={(e) => {
                e.currentTarget.src = "/logo.png";
              }}
            />
          </div>
          <h1 className="text-2xl font-bold">{schoolInfo?.name}</h1>
          {schoolInfo?.motto && (
            <p className="text-blue-100 italic mt-1">{schoolInfo?.motto}</p>
          )}
        </div>

        {/* Login Form */}
        <div className="p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Welcome Back
          </h2>
          <p className="text-gray-600 mb-6">Please sign in to your account</p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email Address
              </label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                {...register("email", {
                  required: "Email is required",
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: "Please enter a valid email address",
                  },
                })}
                className={formStyles(!!errors.email, "mt-1")}
                disabled={loading}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-700"
                >
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-sm text-blue-600 hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  {...register("password", {
                    required: "Password is required",
                    minLength: {
                      value: 6,
                      message: "Password must be at least 6 characters",
                    },
                  })}
                  className={formStyles(!!errors.password, "pr-10")}
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.password.message}
                </p>
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  type="checkbox"
                  {...register("rememberMe")}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="remember-me"
                  className="ml-2 block text-sm text-gray-700"
                >
                  Remember me
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition ${
                loading ? "opacity-70 cursor-not-allowed" : ""
              }`}
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Signing in...
                </div>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            Don't have an account?{" "}
            <Link
              href="/register"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              Create account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
