"use client";

import Menu from "@/components/Menu";
import MobileMenu from "@/components/MobileMenu";
import Navbar from "@/components/Navbar";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { UserType } from "@/types/intefaces";
import { getActualPath } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { data: session, status } = useSession() as {
    data: { user: UserType } | null;
    status: string;
  };

  // If session is loading, show a loading indicator
  if (status === "loading") {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="w-8 h-8 rounded-full animate-spin bg-gray-300 mx-auto"></div>
        <style jsx>{`
          @keyframes spin {
            0% {
              transform: rotate(0deg);
            }
            100% {
              transform: rotate(360deg);
            }
          }
          .animate-spin {
            animation: spin 1s linear infinite;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="h-screen max-h-screen flex">
      {/* LEFT */}
      <div className="flex flex-col justify-between w-[9%] lg:w-[15%] xl:w-[14%] max-sm:hidden max-h-screen overflow-hidden">
        <Link
          href={`${getActualPath("/dashboard")}`}
          className="flex items-center justify-center p-2 lg:justify-start gap-2 h-14"
          title={session?.user?.schoolName}
        >
          {session?.user?.schoolLogo ? (
            <img
              src={String(session.user.schoolLogo)}
              alt="LOGO"
              width={32}
              height={32}
              onError={(e) => {
                e.currentTarget.src = "/logo.png";
              }}
            />
          ) : (
            <img src="/logo.png" alt="LOGO" width={32} height={32} />
          )}

          <span className="hidden lg:block font-bold">
            {session?.user?.schoolShortName &&
            session?.user?.schoolShortName !== "None"
              ? session.user.schoolShortName.length > 10
                ? `${session.user.schoolShortName.slice(0, 10)}...`
                : session.user.schoolShortName
              : session?.user?.schoolName && session.user.schoolName.length > 10
              ? `${session.user.schoolName.slice(0, 10)}...`
              : String(session?.user?.schoolName || "FUTA Secondary")}
          </span>
        </Link>
        <div className="flex p-2 flex-1 overflow-auto h-[calc(100vh-60px)]">
          <Menu />
        </div>
      </div>

      {/* RIGHT */}
      <div className="w-[91%] lg:w-[85%] flex-1 max-w-full overflow-x-hidden xl:w-[86%] bg-[#F7F8FA] overflow-scroll flex flex-col max-sm:w-full">
        <MobileMenu />
        <Navbar />
        {children}
      </div>
    </div>
  );
}
