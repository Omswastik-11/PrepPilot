import React from 'react';
import { cn } from "@/lib/utils";

interface ActivityDay {
  date: string;
  count: number;
}

interface HeatmapProps {
  data: ActivityDay[];
}

export function Heatmap({ data }: HeatmapProps) {
  // Build a map for easy lookup
  const countMap = new Map(data.map(d => [d.date, d.count]));

  // Generate last 365 days
  const today = new Date();
  const days = [];
  for (let i = 364; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    const count = countMap.get(dateStr) || 0;
    days.push({ date: dateStr, count });
  }

  // Group into weeks (columns)
  const weeks = [];
  let currentWeek = [];
  
  // Fill the first week with empty slots if it doesn't start on Sunday
  const firstDay = new Date(days[0].date).getDay();
  for (let i = 0; i < firstDay; i++) {
    currentWeek.push(null);
  }

  for (const day of days) {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }
  if (currentWeek.length > 0) {
    // Fill the rest with null
    while (currentWeek.length < 7) {
      currentWeek.push(null);
    }
    weeks.push(currentWeek);
  }

  const getColor = (count: number) => {
    if (count === 0) return 'bg-[var(--muted)] border-[var(--border)]';
    if (count === 1) return 'bg-emerald-900 border-emerald-800';
    if (count <= 3) return 'bg-emerald-600 border-emerald-500';
    return 'bg-emerald-400 border-emerald-300';
  };

  return (
    <div className="w-full overflow-x-auto pb-4">
      <div className="flex gap-1 min-w-max">
        {weeks.map((week, wIndex) => (
          <div key={wIndex} className="flex flex-col gap-1">
            {week.map((day, dIndex) => {
              if (!day) return <div key={dIndex} className="w-3 h-3 rounded-[2px]" />;
              return (
                <div
                  key={dIndex}
                  title={`${day.count} interviews on ${day.date}`}
                  className={cn(
                    "w-3 h-3 rounded-[2px] border transition-colors hover:ring-1 hover:ring-emerald-400 hover:ring-offset-1 hover:ring-offset-[var(--background)]",
                    getColor(day.count)
                  )}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
