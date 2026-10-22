# Security policy

Report security issues privately to the repository owner. Do not open a public issue containing credentials, restricted provider data, or a working exploit.

The application validates Clerk JWT signatures and claims, restricts CORS, caps request bodies, rate-limits API traffic, and separates administrator routes. Production secrets belong only in Render, Cloudflare, Neon, Clerk, Sentry, and GitHub environment secret stores. They must never be placed in frontend variables unless explicitly designed to be public, such as the Clerk publishable key.

Provider downloads can contain license-restricted material. Raw Space-Track and DISCOS inputs are immutable private artifacts and are never exposed by public endpoints.
