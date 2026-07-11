# Changelog

## 2026-06-10

### Culture Raiding — fairer loot even for lost attacks

When attacking another empire, culture is now stolen even if the attack fails —
as long as the defender lost lives in the process.

**New calculation:**

The stolen culture amount consists of two parts:

1. **Lives share** (always applies, even on attacker defeat):
   `defender's lost lives × era factor × rate`
   The more lives the defender lost and the more advanced their era, the more
   culture is stolen.

2. **Pool share** (only on attacker victory):
   Additionally a random percentage (1–5%) of the defender's total culture pool.

**Era penalty:** If a player attacks an empire in a lower era, they receive only
50% of the stolen culture — cultural progress protects.
