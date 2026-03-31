import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Legend } from 'recharts'
import type { CompanyDnaResponse, SegmentBenchmark } from '../../types/companyDna'

interface DnaRadarChartProps {
  dna: CompanyDnaResponse
  benchmark: SegmentBenchmark | null
}

export default function DnaRadarChart({ dna, benchmark }: DnaRadarChartProps) {
  const data = [
    {
      axis: '기술 다양성',
      company: dna.tech.diversityScore,
      benchmark: benchmark?.avgTechScore ?? 50,
    },
    {
      axis: '채용 강도',
      company: dna.hiring.intensityScore,
      benchmark: benchmark?.avgHiringScore ?? 50,
    },
    {
      axis: '연봉 포지션',
      company: dna.compensation.positionPercentile ?? 50,
      benchmark: 50,
    },
    {
      axis: '조직 문화',
      company: dna.culture.cultureScore,
      benchmark: benchmark?.avgCultureScore ?? 50,
    },
  ]

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid />
          <PolarAngleAxis dataKey="axis" tick={{ fontSize: 12 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Radar
            name={dna.companyName}
            dataKey="company"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.3}
          />
          <Radar
            name="세그먼트 평균"
            dataKey="benchmark"
            stroke="#9ca3af"
            fill="#9ca3af"
            fillOpacity={0.1}
          />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
