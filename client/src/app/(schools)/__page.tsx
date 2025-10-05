"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const SchoolPage = () => {
  const [schoolCode, setSchoolCode] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (schoolCode.trim()) {
      router.push(`/schools/${schoolCode}/login`);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        background: "linear-gradient(to right, #4a0694, #005eff)",
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="flex flex-col items-center bg-white p-8 rounded-lg shadow-lg"
      >
        <h1 className="text-3xl mb-6 font-bold text-gray-800">
          Enter School Short-Name or Code
        </h1>
        <input
          type="text"
          value={schoolCode}
          onChange={(e) => setSchoolCode(e.target.value)}
          placeholder="School Code"
          className="p-3 text-lg mb-5 border border-gray-300 rounded w-full"
        />
        <button
          type="submit"
          className="p-3 px-6 text-lg bg-blue-500 text-white rounded hover:bg-blue-600 transition duration-300"
        >
          Submit
        </button>
      </form>
    </div>
  );
};

export default SchoolPage;
