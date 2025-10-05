"use client";

import React from "react";
import Image from "next/image";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { customSignOut } from "@/actions/auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Link from "next/link";

const Navbar = () => {
  const { data: session, status } = useSession();
  const router = useRouter();
  const isLoading = status === "loading";

  const handleSignOut = async () => {
    try {
      // Clear client-side auth state
      await signOut({
        callbackUrl: "/login",
        redirect: false,
      });

      // Clear client-side subdomain storage
      if (typeof window !== "undefined") {
        document.cookie =
          "school_subdomain=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC";
        sessionStorage.removeItem("school_subdomain");
      }

      // Call server-side sign out
      await customSignOut();

      // Force a full page reload to clear any remaining state
      window.location.href = "/login";
    } catch (error) {
      console.error("Error during sign out:", error);
    }
  };

  // Don't render anything while loading to avoid layout shift
  if (isLoading) return null;

  // If no session, don't show the navbar
  if (!session) {
    return null;
  }

  const user = session.user;
  const userInitials = user?.fullName
    ? user.fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
    : "U";

  return (
    <div className="flex items-center justify-between p-4 bg-white shadow-sm">
      {/* SEARCH BAR - Only show for authenticated users */}
      <div className="hidden md:flex items-center gap-2 text-xs rounded-full ring-1 ring-gray-300 px-3 py-1.5">
        <Image
          src="/search.png"
          alt="Search"
          width={14}
          height={14}
          className="opacity-60"
        />
        <input
          type="text"
          placeholder="Search..."
          className="w-[200px] bg-transparent outline-none text-sm text-gray-700 placeholder-gray-400"
        />
      </div>

      {/* ICONS AND USER */}
      <div className="flex items-center gap-4">
        {/* Messages */}
        <button
          className="p-1.5 rounded-full hover:bg-gray-100 transition-colors relative"
          aria-label="Messages"
          onClick={() => router.push("/messages")}
        >
          <Image
            src="/message.png"
            alt="Messages"
            width={20}
            height={20}
            className="opacity-70"
          />
        </button>

        {/* Notifications */}
        <button
          className="p-1.5 rounded-full hover:bg-gray-100 transition-colors relative"
          aria-label="Notifications"
          onClick={() => router.push("/notifications")}
        >
          <Image
            src="/announcement.png"
            alt="Notifications"
            width={20}
            height={20}
            className="opacity-70"
          />
          <div className="absolute -top-1 -right-1 w-5 h-5 flex items-center justify-center bg-purple-500 text-white rounded-full text-xs">
            0
          </div>
        </button>

        {/* User Profile Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-2 p-1 rounded-full hover:bg-gray-100 transition-colors"
              aria-label="User menu"
            >
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-medium text-gray-700">
                {user?.image ? (
                  <Image
                    src={user.image}
                    alt={user.fullName || "User"}
                    width={32}
                    height={32}
                    className="rounded-full object-cover w-full h-full"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.onerror = null;
                      target.src = "/avatar.png";
                    }}
                  />
                ) : (
                  <span>{userInitials}</span>
                )}
              </div>
              <span className="hidden md:inline text-sm font-medium text-gray-700">
                {user?.fullName || "User"}
              </span>
              <svg
                className="w-4 h-4 text-gray-500 hidden md:block"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {user?.fullName || "User"}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.email || ""}
                </p>
                <p className="text-xs leading-none text-muted-foreground capitalize">
                  {user?.role?.toLowerCase() || "user"}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem asChild>
                <Link href="/profile" className="w-full cursor-pointer">
                  Your Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/settings" className="w-full cursor-pointer">
                  Settings
                </Link>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleSignOut}
              className="cursor-pointer text-red-600 focus:bg-red-50 focus:text-red-600"
            >
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

export default Navbar;
