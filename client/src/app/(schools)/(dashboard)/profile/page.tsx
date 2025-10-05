"use client";

import React from "react";
import { useSession } from "next-auth/react";
import Image from "next/image";
import { UserType } from "@/types/intefaces";

const ProfilePage = () => {
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
    return <div>Please log in to view your profile.</div>;
  }

  const user = session.user as UserType;

  return (
    <div className="p-4 flex gap-4 flex-col md:flex-row">
      {/* LEFT - PROFILE CARD */}
      <div className="w-full lg:w-1/3 p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <Image
            src={user?.image || "/avatar.png"}
            alt="User Avatar"
            width={120}
            height={120}
            className="rounded-full mx-auto mb-4"
          />
          <h3 className="text-lg font-semibold">{user?.fullName}</h3>
          <p className="text-sm text-gray-500">{user?.email}</p>
        </div>
        <div className="mt-6">
          <h4 className="font-semibold mb-2">Details</h4>
          <ul className="text-sm text-gray-600 space-y-2">
            <li>
              <strong>Role:</strong> {user?.role}
            </li>
            <li>
              <strong>Phone:</strong> {user?.phone || "N/A"}
            </li>
            <li>
              <strong>Address:</strong> {user?.address || "N/A"}
            </li>
          </ul>
        </div>
      </div>

      {/* RIGHT - PROFILE DETAILS */}
      <div className="w-full lg:w-2/3 p-6 bg-white rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">Personal Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Name
            </label>
            <input
              type="text"
              value={user?.fullName || ""}
              readOnly
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              type="email"
              value={user?.email}
              readOnly
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Phone
            </label>
            <input
              type="text"
              value={user?.phone || ""}
              readOnly
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Address
            </label>
            <textarea
              value={user?.address || ""}
              readOnly
              rows={3}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
