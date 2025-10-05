// app/register/page.tsx (server component)
import React from "react";
import RegisterComponent from "./RegisterComponent";
import { redirect } from "next/navigation";
import { getCanonicalUrlServer } from "@/actions/getHostInfo";

const Register: React.FC = async () => {
  // Defensive fallback: only redirect if host must change
  const canonical = await getCanonicalUrlServer({ pathname: "/register" });

  console.log(canonical);

  if (canonical?.changed) {
    redirect(canonical.url); // already includes /register and query/hash if any
  }
  return <RegisterComponent />;
};

export default Register;
