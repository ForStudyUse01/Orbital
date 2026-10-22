import { useAuth } from "@clerk/clerk-react";
import { useEffect } from "react";
import App from "./App";
import { configureAccessTokenProvider } from "./api";

export function ClerkApp() {
  const { getToken } = useAuth();
  useEffect(() => {
    configureAccessTokenProvider(() => getToken());
  }, [getToken]);
  return <App />;
}
