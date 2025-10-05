// import { useRouter } from "next/navigation";
import { getSubdomainServer } from "@/actions/getHostInfo";

const Login: React.FC = async () => {
  const subdomain = await getSubdomainServer();

  return <>{["www", "api", "health", "docs"].includes(subdomain || "")}</>;
};

export default Login;
