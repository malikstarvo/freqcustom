export function Sparkline({ data, width = 80, height = 24, color = "#00ff88" }: {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
}) {
  if (!data.length) return <div className="w-20 h-6" />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={width} height={height} className="opacity-80">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth={2}
        points={points}
      />
    </svg>
  );
}
