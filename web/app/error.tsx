"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface to the console; a real analytics sink can hook in here.
    console.error(error);
  }, [error]);

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center px-6 text-center">
      <h1 className="text-3xl font-bold text-gray-900">Something went wrong</h1>
      <p className="mt-3 max-w-md text-gray-600">
        That&apos;s on us, not you. Please try again — your progress is saved on the server.
      </p>
      <button
        onClick={reset}
        className="mt-8 rounded-full bg-orange-600 px-6 py-3 font-medium text-white transition hover:bg-orange-700"
      >
        Try again
      </button>
    </main>
  );
}
