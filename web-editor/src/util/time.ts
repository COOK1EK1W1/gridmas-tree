export function timeAgo(date: Date) {
  const units = [
    { name: "year", seconds: 31536000 },
    { name: "month", seconds: 2592000 },
    { name: "day", seconds: 86400 },
    { name: "hour", seconds: 3600 },
    { name: "minute", seconds: 60 },
    { name: "second", seconds: 1 }
  ];

  const now = new Date();
  const past = new Date(date);
  const elapsed = Math.floor((now.getTime() - past.getTime()) / 1000);

  for (const unit of units) {
    if (elapsed >= unit.seconds) {
      const value = Math.floor(elapsed / unit.seconds);
      return `${value} ${unit.name}${value > 1 ? "s" : ""} ago`;
    }
  }

  return "just now";
}
