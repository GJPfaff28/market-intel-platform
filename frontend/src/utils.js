export function dedupeSetupMatches(matches) {
  const seen = new Set();
  return matches.filter((m) => {
    const key = `${m.setup_type}-${m.day_number ?? ""}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
