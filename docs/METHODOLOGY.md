# Research methodology

## Population and identity

Population is the count of distinct catalog identifiers present in a snapshot, not a count of element-set rows. The canonical join key is the NORAD catalog ID, stored as `BIGINT`; the international designator is the second choice, and reviewed aliases are the last choice. Source classifications remain available beside the normalized classification.

Normalized composition is active payload, inactive payload, debris, rocket body, or unknown. Payload does not imply active. Modeled sub-catalog debris estimates remain a separate statistical layer and are never blended into tracked-object totals.

## Time and snapshots

All times are UTC. Production scheduling creates annual January 1 snapshots for 1957–1999, monthly first-of-month snapshots from 2000 onward, and weekly snapshots within 180 days of selected major events. For each object, the newest element at or before the target instant is selected. Records up to 30 days old are normal; records 31–90 days old are explicitly stale; older records are excluded from positional analysis but may remain in catalog-level counts with a reason.

Historical views are snapshots, not continuous measured tracks. The interface must not interpolate between monthly points as though those positions were observations.

## Orbital calculations and regimes

Semi-major axis is derived from mean motion using the standard Earth gravitational parameter. Perigee and apogee are derived from semi-major axis and eccentricity and cross-checked against source values. The classifier is implemented and boundary-tested in `oei_pipeline.analytics`.

- LEO: apogee at or below 2,000 km.
- MEO: perigee above 2,000 km and apogee below 35,586 km.
- GEO: mean altitude within 35,786 ± 200 km, eccentricity at most 0.05, inclination at most 15°.
- GTO/HEO: crosses the GEO region or has eccentricity at least 0.25 after GEO is excluded.
- Super-GEO: perigee above 35,986 km.
- Other: remaining Earth-bound orbits.

## Concentration and persistence

Production concentration grids use 50 km altitude bins through 2,000 km, 250 km bins from 2,000–40,000 km plus overflow, and 5° inclination bins. Raw count, population share, time change, and approximate shell-volume-normalized density are separate measures. None is a collision probability.

Persistence is measured from first valid observation to confirmed decay. Still-observed objects are right-censored. Kaplan–Meier estimates are compared by normalized class, orbital regime, and launch cohort; every chart explains censoring.

## Event analysis

Events include source-supported parent objects and mapped fragment cohorts. Comparisons use 30-, 90-, and 365-day windows and describe the affected altitude/inclination region plus subsequent fragment persistence. Deep studies cover Fengyun-1C, Iridium 33–Cosmos 2251, and Cosmos 1408.

## Limitations

Catalogs omit classified and untracked objects and have changing sensor, policy, and catalog-maintenance characteristics. Markers are enlarged. OEI is educational environmental analytics—not navigation, conjunction assessment, collision probability, avoidance advice, or an official risk rating.
