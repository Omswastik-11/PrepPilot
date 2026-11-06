import React from 'react';

interface ScoreTrendProps {
  scores: number[];
}

export function ScoreTrend({ scores }: ScoreTrendProps) {
  if (!scores || scores.length < 2) {
    return (
      <div className="h-full flex items-center justify-center text-xs text-[var(--muted-foreground)]">
        Not enough data
      </div>
    );
  }

  // Draw sparkline
  const width = 100;
  const height = 40;
  const maxScore = 10;
  const step = width / (scores.length - 1);
  const scale = height / maxScore;

  const points = scores.map((s, i) => `${i * step},${height - s * scale}`).join(' ');

  return (
    <div className="w-full h-full flex items-center justify-center pt-2">
      <svg width="100%" height="100%" viewBox={`0 -5 ${width} ${height + 15}`} preserveAspectRatio="none" className="overflow-visible group">
        <polyline 
          points={points} 
          fill="none" 
          stroke="#ffa116" 
          strokeWidth="1.5" 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          className="drop-shadow-sm transition-all duration-300"
        />
        {scores.map((s, i) => {
          const isLast = i === scores.length - 1;
          return (
            <g key={i} className="group-hover:opacity-100 transition-opacity">
              {/* Invisible larger circle for hover target if needed, or just styling */}
              <circle 
                cx={i * step} 
                cy={height - s * scale} 
                r={isLast ? "2.5" : "1.5"} 
                fill={isLast ? "#ffffff" : "#282828"} 
                stroke="#ffa116" 
                strokeWidth={isLast ? "1.5" : "1"}
                className={!isLast ? "opacity-0 group-hover:opacity-100 transition-opacity duration-300" : ""}
              />
              <title>Score: {s.toFixed(1)}</title>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
