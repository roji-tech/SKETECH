"use client";

import React from "react";
import { LanndingPageHeader } from "@/components/headers/HomeHeader";

export default function AuthPage({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="flex flex-col justify-between min-h-screen">
      <LanndingPageHeader />

      <div className="w-full lg:grid lg:min-h-[calc(100vh-80px)] lg:grid-cols-[1fr_1.1fr] text-black">
        <div
          className="bg-slate-700 flex flex-1 items-center justify-center bg-no-repeat max-lg:fixed max-lg:inset-0 max-lg:-bottom-4 max-lg:-z-10 filter brightness-75"
          style={{
            backgroundImage: "url(logo.png)",
            backgroundRepeat: "no-repeat",
            backgroundSize: "contain",
            backgroundPosition: "center",
            // border: "15px solid #000",
          }}
        />

        <div className="flex items-center justify-center p-6 bg-secondary-600 max-lg:min-h-[calc(100vh-80px)] max-lg:backdrop-brightness-75">
          {children}
        </div>
      </div>
    </div>
  );
}
