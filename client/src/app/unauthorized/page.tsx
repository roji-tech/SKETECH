// src/app/unauthorized/page.tsx
import Link from "next/link";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function UnauthorizedPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  // Next 15: searchParams is a Promise
  const params = await searchParams;

  const first = (v?: string | string[]) => (Array.isArray(v) ? v[0] : v);

  const message =
    first(params.message) ?? "You do not have permission to access this page.";
  const callbackUrl = first(params.callbackUrl) ?? "/";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md text-center">
        <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Access Denied</h1>
        <p className="text-gray-600 mb-6">{message}</p>

        <div className="flex flex-col space-y-3">
          <Link
            href="/login"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-center"
          >
            Go to Login
          </Link>

          <Link
            href={callbackUrl}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors text-center"
          >
            Go Back
          </Link>

          <Link
            href="/"
            className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
          >
            Return to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
