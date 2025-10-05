"use client";

import React from "react";

import { useSession } from "next-auth/react";
import Announcements from "@/components/Announcements";
import AttendanceChart from "@/components/AttendanceChart";
import CountChart from "@/components/CountChart";
import EventCalendar from "@/components/EventCalendar";
import FinanceChart from "@/components/FinanceChart";
import UserCard from "@/components/UserCard";

const DashboardPage = () => {
  const { data: session, status } = useSession();

  // If session is loading, show a loading indicator
  if (status === "loading") {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <img
            src="/path-to-your-logo.png"
            alt="School Logo"
            className="w-24 h-24 mx-auto mb-4 animate-spin"
          />
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // If session is not available, show an error or redirect
  if (!session) {
    return <div>Please log in to view the dashboard</div>;
  }

  const userRole = session.user.role; // Assuming role is stored in session.user.role

  return (
    <div className="p-4 flex gap-4 flex-col md:flex-row">
      {/* LEFT */}
      <div className="w-full lg:w-2/3 flex flex-col gap-8">
        {/* USER CARDS */}
        {(userRole === "admin" || userRole === "staff") && (
          <div className="flex gap-4 justify-between flex-wrap">
            {userRole === "admin" && <UserCard type="student" />}
            {userRole === "admin" && <UserCard type="teacher" />}
            {userRole === "admin" && <UserCard type="parent" />}
            {userRole === "admin" && <UserCard type="staff" />}
            {userRole === "staff" && <UserCard type="student" />}
          </div>
        )}

        {/* MIDDLE CHARTS */}
        {(userRole === "admin" || userRole === "staff") && (
          <div className="flex gap-4 flex-col lg:flex-row">
            {/* COUNT CHART */}
            {userRole === "admin" && (
              <div className="w-full lg:w-1/3 h-[450px]">
                <CountChart />
              </div>
            )}
            {/* ATTENDANCE CHART */}
            <div className="w-full lg:w-2/3 h-[450px]">
              <AttendanceChart />
            </div>
          </div>
        )}

        {/* BOTTOM CHART */}
        {userRole === "admin" && (
          <div className="w-full h-[500px]">
            <FinanceChart />
          </div>
        )}
      </div>

      {/* RIGHT */}
      <div className="w-full lg:w-1/3 flex flex-col gap-8">
        <EventCalendar />
        {/* Announcements for all roles */}
        <Announcements />
      </div>
    </div>
  );
};

export default DashboardPage;
