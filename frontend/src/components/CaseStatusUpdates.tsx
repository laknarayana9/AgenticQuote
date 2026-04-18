'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useWebSocket } from '@/hooks/useWebSocket'
import { CheckCircle, Clock, AlertTriangle, FileText } from 'lucide-react'

interface CaseUpdate {
  caseId: string
  status: 'pending' | 'in_review' | 'approved' | 'rejected' | 'needs_info'
  timestamp: number
  message: string
}

export function CaseStatusUpdates() {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
  const { isConnected, lastMessage } = useWebSocket(wsUrl)
  const [recentUpdates, setRecentUpdates] = useState<CaseUpdate[]>([])

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'case_update') {
      const update: CaseUpdate = lastMessage.data
      setRecentUpdates(prev => [update, ...prev].slice(0, 10))
    }
  }, [lastMessage])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'rejected':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'in_review':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'needs_info':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />
      default:
        return <FileText className="h-4 w-4 text-slate-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'text-green-600 dark:text-green-400'
      case 'rejected':
        return 'text-red-600 dark:text-red-400'
      case 'in_review':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'needs_info':
        return 'text-orange-600 dark:text-orange-400'
      default:
        return 'text-slate-600 dark:text-slate-400'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Real-Time Case Updates</CardTitle>
            <CardDescription>Live case status changes</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recentUpdates.length === 0 ? (
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Waiting for updates...
            </p>
          ) : (
            recentUpdates.map((update) => (
              <div
                key={`${update.caseId}-${update.timestamp}`}
                className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50"
              >
                <div className="mt-0.5">{getStatusIcon(update.status)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">Case #{update.caseId}</p>
                    <span className="text-xs text-slate-600 dark:text-slate-400">
                      {new Date(update.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className={`text-sm ${getStatusColor(update.status)} capitalize`}>
                    {update.status.replace('_', ' ')}
                  </p>
                  {update.message && (
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                      {update.message}
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
