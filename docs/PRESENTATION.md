# Presentation guide

## Five-minute narrative

1. Start on Overview: “A catalog is a list; this project treats the list as an environment.”
2. Show Population Evolution and distinguish tracked counts from modeled debris.
3. Open Concentration and explain altitude/inclination structure rather than individual dots.
4. Open the 3D Environment, filter debris, jump to an event-era snapshot, and state that historical frames are discrete validated snapshots.
5. Open an event and Persistence to connect a short event with a long environmental consequence.
6. Save a workspace, create a read-only link, and end on Methodology/provenance.

## Offline fallback

Keep the CI `presentation-safe-web-build` artifact, a local API environment, and a screen recording on the presentation laptop. Before presenting, run `uv run --project apps/api uvicorn oei_api.main:app --port 8000` and `pnpm --filter @oei/web preview`; verify both while disconnected from Wi-Fi.

## Required verbal caveat

“This visualizes tracked catalog objects and separately labeled modeled estimates. It does not show every physical object and is not a collision-risk or navigation system.”
