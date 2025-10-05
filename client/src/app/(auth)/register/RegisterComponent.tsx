"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation"; // Import useRouter for navigation
import { useForm, SubmitHandler } from "react-hook-form";
import axios from "axios";
import { signIn } from "next-auth/react";
import { toast } from "react-hot-toast";
import Link from "next/link";
import { API_URL } from "../../../../config";
import { apiPost, setSubdomain } from "@/actions/fetchApi";

// Define type for signup form data
type SignupFormInputs = {
  firstName: string;
  lastName: string;
  email: string;
  gender: string;
  schoolName: string;
  schoolPhone: string;
  schoolEmail: string;
  schoolAddress: string;
  subdomain: string;
  password: string;
  confirmPassword: string;
};

// Helper function to handle subdomains and Vercel-style domains
const getSubdomainUrl = (subdomain: string, path: string = "") => {
  // Get the current protocol, hostname and port
  const protocol = window.location.protocol;
  const hostname = window.location.hostname;
  const port = window.location.port ? `:${window.location.port}` : "";

  // Remove 'www.' if present
  const cleanHost = hostname.replace(/^www\./i, "");

  // Handle Vercel preview URLs (e.g., you.vercel.app, school.you.vercel.app)
  const isVercelApp = cleanHost.endsWith(".vercel.app");
  const isVercelPreview =
    cleanHost.endsWith(".vercel.app") && cleanHost.split(".").length > 3;

  console.log(isVercelApp, isVercelPreview, port, cleanHost, subdomain);

  // If it's a Vercel preview URL and not already a subdomain, add the subdomain
  if (isVercelApp && !isVercelPreview) {
    return `${protocol}//${subdomain}.${cleanHost}${port}${path}`;
  }

  // For regular domains, replace the first part with the subdomain
  const domainParts = cleanHost.split(".");
  // If it's a Vercel preview with existing subdomain, replace the first part
  const baseDomain = isVercelPreview
    ? cleanHost.split(".").slice(1).join(".")
    : cleanHost;

  return `${protocol}//${subdomain}.${baseDomain}${port}${path}`;
};

export default function RegisterComponent() {
  const router = useRouter(); // Initialize useRouter for navigation
  const [loading, setLoading] = useState(false); // State to manage loading status

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SignupFormInputs>();

  const password = watch("password");

  const onSubmit: SubmitHandler<SignupFormInputs> = async (data) => {
    setLoading(true);

    // Client-side validation for password match
    if (data.password !== data.confirmPassword) {
      toast.error("Passwords do not match");
      setLoading(false);
      return;
    }

    const payload = {
      first_name: data.firstName.trim(),
      last_name: data.lastName.trim(),
      email: data.email.trim().toLowerCase(),
      password: data.password,
      gender: data.gender,
      school_name: data.schoolName.trim(),
      school_phone: data.schoolPhone.trim(),
      school_email: data.schoolEmail.trim().toLowerCase(),
      school_address: data.schoolAddress.trim(),
      subdomain: data.subdomain.trim().toLowerCase(),
    };

    try {
      await setSubdomain(data.subdomain);
      sessionStorage.setItem("school_subdomain", data.subdomain);
      const response = await apiPost("/auth/users/", payload, {
        no_auth: true,
      });

      console.log(response);

      if (response.success) {
        toast.success(
          "School registration successful! Setting up your account..."
        );

        // Registration successful, now sign in using next-auth
        const signInResponse = await signIn("credentials", {
          redirect: false,
          email: data.email.trim().toLowerCase(),
          password: data.password,
        });

        if (signInResponse?.ok) {
          // Inside the onSubmit function, after successful registration:
          // Store subdomain in both cookies and sessionStorage
          document.cookie = `school_subdomain=${
            data.subdomain
          }; path=/; max-age=${60 * 60 * 24 * 30}`; // 30 days
          if (typeof window !== "undefined") {
            sessionStorage.setItem("school_subdomain", data.subdomain);
          }

          toast.success("Registration successful! Redirecting...");
          // Use window.location for full page reload to ensure all auth state is properly set
          const redirectUrl = process.env.NEXT_PUBLIC_NO_SUBDOMAIN
            ? "/signup-success"
            : getSubdomainUrl(data.subdomain, "/signup-success");
          window.location.href = redirectUrl;
        } else {
          // If sign-in fails, redirect to login page
          toast.success("Account created successfully! Please sign in.");
          const redirectUrl = process.env.NEXT_PUBLIC_NO_SUBDOMAIN
            ? "/login"
            : getSubdomainUrl(data.subdomain, "/login");
          window.location.href = redirectUrl;
        }
      } else {
        console.log(response);
        // Handle API errors
        const errorData = response.error;

        if (typeof errorData === "object") {
          // Handle field-specific errors
          Object.entries(errorData).forEach(([field, errors]) => {
            const errorMessages = Array.isArray(errors) ? errors : [errors];
            errorMessages.forEach((errorMsg: string) => {
              // Format field name for display (e.g., first_name -> First Name)
              const formattedField = field
                .split("_")
                .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                .join(" ");

              // Special handling for password errors to make them more user-friendly
              if (field === "password") {
                if (errorMsg.includes("too short")) {
                  toast.error("Password must be at least 8 characters long");
                } else if (errorMsg.includes("too common")) {
                  toast.error(
                    "Password is too common. Please choose a stronger password."
                  );
                } else if (errorMsg.includes("entirely numeric")) {
                  toast.error("Password cannot be entirely numeric.");
                } else if (errorMsg.includes("similar to")) {
                  toast.error(
                    "Password is too similar to your personal information."
                  );
                } else {
                  toast.error(`Password: ${errorMsg}`);
                }
              } else {
                toast.error(`${formattedField}: ${errorMsg}`);
              }
            });
          });
        } else if (response.message) {
          // Handle general error message
          toast.error(response.message);
        } else {
          // Fallback error message
          toast.error(
            "An error occurred during registration. Please check your information and try again."
          );
        }
      }
    } catch (error: any) {
      console.error("Registration error:", error);

      // Handle network errors
      if (error.message?.includes("Network Error")) {
        toast.error(
          "Unable to connect to the server. Please check your internet connection and try again."
        );
      } else if (error.request) {
        // The request was made but no response was received
        toast.error("The server is not responding. Please try again later.");
      } else if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        const { status, data } = error.response;

        if (status === 400) {
          // Bad request - validation errors
          if (data && typeof data === "object") {
            Object.entries(data).forEach(([field, errors]) => {
              const errorMessages = Array.isArray(errors) ? errors : [errors];
              errorMessages.forEach((errorMsg: string) => {
                toast.error(`${field}: ${errorMsg}`);
              });
            });
          } else {
            toast.error(
              "Invalid data provided. Please check your information and try again."
            );
          }
        } else if (status === 409) {
          // Conflict - duplicate entry
          toast.error(
            "This email or subdomain is already registered. Please use different credentials."
          );
        } else if (status >= 500) {
          // Server error
          toast.error(
            "A server error occurred. Our team has been notified. Please try again later."
          );
        } else {
          // Other errors
          toast.error(`An error occurred (${status}). Please try again.`);
        }
      } else {
        // Something happened in setting up the request that triggered an Error
        toast.error("An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const formStyles = (condition: any, otherStyles = "") =>
    `w-full px-4 py-2 border rounded-sm outline outline-none hover:outline-[0.5px] ${
      condition ? "border-red-500" : "border-none"
    } bg-[#FAF7EE] ${otherStyles}`;

  return (
    <div className="flex items-center justify-center">
      <div className="w-full max-w-lg bg-white p-8 rounded-lg">
        <h2 className="text-2xl font-bold mb-4">Create an account</h2>
        <p className="text-sm mb-6">
          You already have an account?{" "}
          <Link href="/login" className="text-blue-500 underline">
            Login
          </Link>
        </p>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="space-y-4"
          method="post"
        >
          <div className="flex space-x-4">
            <div className="w-1/2">
              <input
                type="text"
                placeholder="First Name"
                {...register("firstName", {
                  required: "First name is required",
                })}
                className={formStyles(errors.firstName)}
              />
              {errors.firstName && (
                <p className="text-red-500 text-xs mt-1">
                  {errors.firstName.message}
                </p>
              )}
            </div>
            <div className="w-1/2">
              <input
                type="text"
                placeholder="Last Name"
                {...register("lastName", { required: "Last name is required" })}
                className={formStyles(errors.lastName)}
              />
              {errors.lastName && (
                <p className="text-red-500 text-xs mt-1">
                  {errors.lastName.message}
                </p>
              )}
            </div>
          </div>
          <input
            type="email"
            placeholder="Email Address"
            {...register("email", {
              required: "Email is required",
            })}
            className={formStyles(errors.email)}
          />
          {errors.email && (
            <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>
          )}
          <select
            {...register("gender", { required: "Gender is required" })}
            className={formStyles(errors.gender)}
          >
            <option value="">Select Gender</option>
            <option value="M">Male</option>
            <option value="F">Female</option>
          </select>
          {errors.gender && (
            <p className="text-red-500 text-xs mt-1">{errors.gender.message}</p>
          )}
          <input
            type="text"
            placeholder="School Name"
            {...register("schoolName", { required: "School name is required" })}
            className={formStyles(errors.schoolName)}
          />
          {errors.schoolName && (
            <p className="text-red-500 text-xs mt-1">
              {errors.schoolName.message}
            </p>
          )}
          <input
            type="text"
            placeholder="School Phone"
            {...register("schoolPhone", {
              required: "School phone is required",
            })}
            className={formStyles(errors.schoolPhone)}
          />
          {errors.schoolPhone && (
            <p className="text-red-500 text-xs mt-1">
              {errors.schoolPhone.message}
            </p>
          )}
          <input
            type="email"
            placeholder="School Email"
            {...register("schoolEmail", {
              required: "School email is required",
            })}
            className={formStyles(errors.schoolEmail)}
          />
          {errors.schoolEmail && (
            <p className="text-red-500 text-xs mt-1">
              {errors.schoolEmail.message}
            </p>
          )}
          <textarea
            placeholder="School Address"
            rows={3}
            {...register("schoolAddress", {
              required: "School address is required",
            })}
            className={`${formStyles(errors.schoolAddress)} resize-none`}
          />
          {errors.schoolAddress && (
            <p className="text-red-500 text-xs mt-1">
              {errors.schoolAddress.message}
            </p>
          )}
          <input
            type="text"
            placeholder="Subdomain (e.g., myschool)"
            {...register("subdomain", {
              required: "Subdomain is required",
              pattern: {
                value: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
                message:
                  "Subdomain can only contain lowercase letters, numbers, and hyphens",
              },
              minLength: {
                value: 3,
                message: "Subdomain must be at least 3 characters",
              },
              maxLength: {
                value: 63,
                message: "Subdomain must be less than 64 characters",
              },
            })}
            className={formStyles(errors.subdomain)}
          />
          {errors.subdomain && (
            <p className="text-red-500 text-xs mt-1">
              {errors.subdomain.message}
            </p>
          )}
          <div className="flex space-x-4">
            <div className="w-1/2">
              <input
                type="password"
                placeholder="Password"
                {...register("password", {
                  required: "Password is required",
                  minLength: {
                    value: 8,
                    message: "Password must be at least 8 characters",
                  },
                })}
                className={formStyles(errors.password)}
              />
              {errors.password && (
                <p className="text-red-500 text-xs mt-1">
                  {errors.password.message}
                </p>
              )}
            </div>
            <div className="w-1/2">
              <input
                type="password"
                placeholder="Confirm Password"
                {...register("confirmPassword", {
                  validate: (value) =>
                    value === password || "Passwords do not match",
                })}
                className={formStyles(errors.confirmPassword)}
              />
              {errors.confirmPassword && (
                <p className="text-red-500 text-xs mt-1">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>
          </div>
          <button
            type="submit"
            className={`w-full py-2 rounded-lg ${
              loading ? "bg-gray-400" : "bg-blue-600"
            } text-white`}
            disabled={loading}
          >
            {loading ? "Submitting..." : "Register My School"}
          </button>
        </form>
      </div>
    </div>
  );
}
