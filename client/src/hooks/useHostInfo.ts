import { useState, useEffect } from "react";
import { getHostInfoClient, getWwwHostClient, getWwwUrlClient, redirectToWwwClient } from "@/lib/client-host-info";

/**
 * Client-side hook for React components to get subdomain with reactivity
 */
export function useHostInfo(): {
  subdomain: string | null;
  isLoading: boolean;
  hostInfo: ReturnType<typeof getHostInfoClient>;
} {
  const [subdomain, setSubdomain] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hostInfo, setHostInfo] = useState<
    ReturnType<typeof getHostInfoClient>
  >({
    host: null,
    subdomain: null,
    domain: null,
    port: null,
    protocol: null,
    fullUrl: null,
  });

  useEffect(() => {
    const info = getHostInfoClient();
    setSubdomain(info.subdomain);
    setHostInfo(info);
    setIsLoading(false);

    // Listen for URL changes (useful for SPAs)
    const handleLocationChange = () => {
      const newInfo = getHostInfoClient();
      setSubdomain(newInfo.subdomain);
      setHostInfo(newInfo);
    };

    // Listen to popstate for browser back/forward
    window.addEventListener("popstate", handleLocationChange);

    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, []);

  return { subdomain, isLoading, hostInfo };
}

// =============================================================================
// REACT HOOKS
// =============================================================================

/**
 * React hook to get www URL with reactivity
 */
export function useWwwUrl(preservePath: boolean = true): {
  wwwUrl: string | null;
  wwwHost: string | null;
  isSubdomain: boolean;
  isLoading: boolean;
  redirectToWww: () => void;
} {
  const [wwwUrl, setWwwUrl] = useState<string | null>(null);
  const [wwwHost, setWwwHost] = useState<string | null>(null);
  const [isSubdomain, setIsSubdomain] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined") {
      setIsLoading(false);
      return;
    }

    const updateWwwInfo = () => {
      const currentWwwUrl = getWwwUrlClient(preservePath);
      const currentWwwHost = getWwwHostClient();
      const hasSubdomain = window.location.host !== currentWwwHost;

      setWwwUrl(currentWwwUrl);
      setWwwHost(currentWwwHost);
      setIsSubdomain(hasSubdomain);
      setIsLoading(false);
    };

    updateWwwInfo();

    // Listen for URL changes
    const handleLocationChange = () => {
      updateWwwInfo();
    };

    window.addEventListener("popstate", handleLocationChange);

    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, [preservePath]);

  const redirectToWww = () => {
    redirectToWwwClient(preservePath);
  };

  return {
    wwwUrl,
    wwwHost,
    isSubdomain,
    isLoading,
    redirectToWww,
  };
}
