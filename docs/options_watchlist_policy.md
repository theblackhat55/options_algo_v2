# Options Watchlist Policy

## Should options volume be part of Stage A?
Yes.

But options volume should be one part of an options viability score, not the sole screener.

---

## Why Include Options Volume?
Options volume helps identify:
- active names
- contracts likely to be tradeable
- underlyings with current derivatives participation

---

## Why Not Use Options Volume Alone?
Options volume alone can be misleading:
- event spikes
- isolated unusual flow
- poor spread quality
- low open interest
- weak underlying setup

---

## Recommended Options Viability Score Components
1. total options volume
2. open interest
3. bid/ask quality
4. count of viable contracts near target DTE
5. real quote availability
6. greek completeness
7. strike density
8. expiration availability

---

## Recommended Policy
Use:
- underlying quality score
- options viability score
- combined watchlist score

Only symbols that score well on both should proceed to full strategy evaluation.

---

## Production Principle
The watchlist is not just:
- "interesting stocks"

It is:
- "interesting stocks with tradeable options right now"
