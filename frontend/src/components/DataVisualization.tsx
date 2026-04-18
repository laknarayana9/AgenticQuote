'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

interface ChartData {
  name: string
  value: number
  [key: string]: string | number
}

export function DataVisualization() {
  // Sample data - would come from API in production
  const caseVolumeData: ChartData[] = [
    { name: 'Mon', value: 120, approved: 95, rejected: 25 },
    { name: 'Tue', value: 145, approved: 115, rejected: 30 },
    { name: 'Wed', value: 132, approved: 108, rejected: 24 },
    { name: 'Thu', value: 178, approved: 142, rejected: 36 },
    { name: 'Fri', value: 156, approved: 128, rejected: 28 },
    { name: 'Sat', value: 89, approved: 72, rejected: 17 },
    { name: 'Sun', value: 67, approved: 55, rejected: 12 },
  ]

  const riskDistributionData: ChartData[] = [
    { name: 'Low Risk', value: 45 },
    { name: 'Medium Risk', value: 30 },
    { name: 'High Risk', value: 15 },
    { name: 'Very High Risk', value: 10 },
  ]

  const processingTimeData: ChartData[] = [
    { name: 'Week 1', value: 4.5 },
    { name: 'Week 2', value: 4.2 },
    { name: 'Week 3', value: 3.8 },
    { name: 'Week 4', value: 3.2 },
    { name: 'Week 5', value: 2.9 },
    { name: 'Week 6', value: 2.5 },
  ]

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Case Volume</CardTitle>
          <CardDescription>Daily case volume and decisions</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={caseVolumeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#0088FE" name="Total Cases" />
              <Bar dataKey="approved" fill="#00C49F" name="Approved" />
              <Bar dataKey="rejected" fill="#FF8042" name="Rejected" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Risk Distribution</CardTitle>
          <CardDescription>Case risk level distribution</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {riskDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Average Processing Time</CardTitle>
          <CardDescription>Processing time trend (minutes)</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={processingTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#0088FE" strokeWidth={2} name="Avg Time (min)" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
