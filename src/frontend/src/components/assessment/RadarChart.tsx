import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'

interface RadarDataPoint {
  subject: string
  score: number
  target?: number
}

interface RadarChartProps {
  data: RadarDataPoint[]
  height?: number
}

export function RadarChart({ data, height = 350 }: RadarChartProps) {
  if (data.length === 0) {
    return null
  }

  const hasTarget = data.some((d) => d.target !== undefined)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fontSize: 11 }}
        />
        <Radar
          name="Текущий уровень"
          dataKey="score"
          stroke="#228be6"
          fill="#228be6"
          fillOpacity={0.4}
        />
        {hasTarget && (
          <Radar
            name="Целевой уровень"
            dataKey="target"
            stroke="#2f9e44"
            fill="#2f9e44"
            fillOpacity={0.15}
            strokeDasharray="5 5"
          />
        )}
        <Tooltip
          formatter={(value: number) => [value.toFixed(2), '']}
        />
        <Legend />
      </RechartsRadarChart>
    </ResponsiveContainer>
  )
}
