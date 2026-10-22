# Current orbital environment

The 3D environment has two explicit modes. **Current / CelesTrak** uses the public
active-satellite GP JSON dataset. **Demo history** retains the deterministic
synthetic snapshots for offline demonstrations. The overview and historical
analytics are still synthetic; this change does not backfill those modules.

There is no trained machine-learning model. Current positions are estimates made
with SGP4, using the source's orbital elements. They are not radar observations.

## Refresh and provenance

`GET /api/v1/environment/current` fetches elements at most once per three hours
while requested. Failed downloads back off for 15 minutes in the running process.
The browser polls the local API every 60 seconds unless auto refresh is disabled.
Propagation runs in a background thread and results are shared for 60 seconds.
This is request-driven refresh, not an unattended scheduler.

Validated records persist to `data/raw/current-active.json` (git-ignored). Writes
use an atomic replacement. A failed refresh keeps the last validated cache and
shows a warning; no cache means HTTP 503, never silent synthetic fallback.
The first fetch needs internet access. The provider may reject requests with 403.
Do not repeatedly retry or attempt to bypass provider restrictions.

Every result includes download time, checksum-derived release identifier, source,
propagation time and exclusion counts. Source downloads over 12 hours old are
marked stale; individual elements over 30 days old are not positioned. Future
epochs within that window may be propagated backward. Objects with SGP4 errors,
non-finite positions or positions inside Earth are excluded.

The active subset is not the complete tracked catalog and must not be used to
infer debris population or operational status outside that source subset.

## Frames and rendering

SGP4 returns TEME coordinates. A Greenwich sidereal-angle rotation supplies an
approximate Earth-fixed frame (no polar-motion correction), then coordinates are
mapped to Three.js y-up: `[ECEF x, ECEF z, -ECEF y] / 6378.137`.
The smooth Earth map stays fixed in that frame. Satellite points are discrete
60-second estimates, not interpolated trajectories. Only the camera may rotate.

One GPU point buffer renders the population; normal blending avoids saturated
white clouds. Pixel ratio is capped at 1; shadows, antialiasing, stars and guide
lines are disabled by default. Demand rendering avoids continuous GPU work when
camera rotation is off. No 30-FPS claim has been benchmarked across hardware.

The interface is inspired by the reference's compact controls, legend and focus
view, not a copy of LeoLabs' assets, sensor beams, proprietary data or branding.

Source: https://celestrak.org/NORAD/documentation/gp-data-formats.php
