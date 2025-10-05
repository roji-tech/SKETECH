// import React from "react";

// // app/register/page.tsx (server component)
// import { redirect } from "next/navigation";
// import { getCanonicalUrlServer } from "@/actions/getHostInfo";

// const Login: React.FC = async () => {
//   // Defensive fallback: only redirect if host must change
//   const canonical = await getCanonicalUrlServer({ pathname: "/login" });

//   console.log(canonical);

//   if (canonical?.changed) {
  //     redirect(canonical.url);
  //   }

import { redirect } from "next/navigation";
import { getSubdomainServer } from "@/actions/getHostInfo";
import { LoginComponent } from "./LoginComponent";

const Login = async () => {
  const subdomain = await getSubdomainServer();

  // If there's no subdomain, redirect to the register page
  if (!subdomain) {
    redirect("/register");
  }

  return <LoginComponent />;
};

export default Login;
