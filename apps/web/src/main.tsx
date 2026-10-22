import { ClerkProvider } from "@clerk/clerk-react";
import * as Sentry from "@sentry/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { ClerkApp } from "./ClerkApp";
import "./styles.css";

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: 1, refetchOnWindowFocus: false } } });
const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const sentryDsn = import.meta.env.VITE_SENTRY_DSN;

if (sentryDsn) Sentry.init({ dsn: sentryDsn, environment: import.meta.env.MODE, tracesSampleRate: 0.1 });

const application = clerkKey
  ? <ClerkProvider publishableKey={clerkKey}><ClerkApp /></ClerkProvider>
  : <App />;

createRoot(document.getElementById("root")!).render(<StrictMode><QueryClientProvider client={queryClient}><BrowserRouter>{application}</BrowserRouter></QueryClientProvider></StrictMode>);
