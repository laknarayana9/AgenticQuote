'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CheckSquare, Square, Play, Download, Trash2, RefreshCw } from 'lucide-react'

interface BulkCase {
  id: string
  caseId: string
  status: string
  riskLevel: string
  selected: boolean
}

export function BulkOperations() {
  const [cases, setCases] = useState<BulkCase[]>([
    { id: '1', caseId: '1001', status: 'pending', riskLevel: 'low', selected: false },
    { id: '2', caseId: '1002', status: 'pending', riskLevel: 'low', selected: false },
    { id: '3', caseId: '1003', status: 'pending', riskLevel: 'medium', selected: false },
    { id: '4', caseId: '1004', status: 'pending', riskLevel: 'low', selected: false },
    { id: '5', caseId: '1005', status: 'pending', riskLevel: 'medium', selected: false },
  ])

  const [selectedOperation, setSelectedOperation] = useState<string>('')

  const toggleSelectAll = () => {
    const allSelected = cases.every(c => c.selected)
    setCases(cases.map(c => ({ ...c, selected: !allSelected })))
  }

  const toggleSelectCase = (caseId: string) => {
    setCases(cases.map(c => 
      c.id === caseId ? { ...c, selected: !c.selected } : c
    ))
  }

  const executeBulkOperation = async () => {
    const selectedCases = cases.filter(c => c.selected)
    console.log(`Executing ${selectedOperation} on ${selectedCases.length} cases`)
  }

  const selectedCount = cases.filter(c => c.selected).length

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bulk Operations</CardTitle>
        <CardDescription>Perform actions on multiple cases</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b pb-4">
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={toggleSelectAll}>
                {cases.every(c => c.selected) ? (
                  <CheckSquare className="h-4 w-4 mr-2" />
                ) : (
                  <Square className="h-4 w-4 mr-2" />
                )}
                Select All
              </Button>
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {selectedCount} selected
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button variant="outline" size="sm" disabled={selectedCount === 0}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            {cases.map((caseItem) => (
              <div
                key={caseItem.id}
                className="flex items-center justify-between p-3 rounded-lg border bg-white dark:bg-slate-800"
              >
                <div className="flex items-center gap-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleSelectCase(caseItem.id)}
                  >
                    {caseItem.selected ? (
                      <CheckSquare className="h-4 w-4" />
                    ) : (
                      <Square className="h-4 w-4" />
                    )}
                  </Button>
                  <div>
                    <p className="font-medium">Case #{caseItem.caseId}</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      Status: {caseItem.status} | Risk: {caseItem.riskLevel}
                    </p>
                  </div>
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-400">
                  Pending
                </div>
              </div>
            ))}
          </div>

          <div className="border-t pt-4">
            <div className="space-y-3">
              <p className="text-sm font-medium">Select Operation:</p>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant={selectedOperation === 'approve' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setSelectedOperation('approve')}
                  disabled={selectedCount === 0}
                >
                  <CheckSquare className='h-4 w-4 mr-2' />
                  Bulk Approve
                </Button>
                <Button
                  variant={selectedOperation === 'reject' ? 'destructive' : 'outline'}
                  size='sm'
                  onClick={() => setSelectedOperation('reject')}
                  disabled={selectedCount === 0}
                >
                  <Trash2 className='h-4 w-4 mr-2' />
                  Bulk Reject
                </Button>
                <Button
                  variant={selectedOperation === 'assign' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setSelectedOperation('assign')}
                  disabled={selectedCount === 0}
                >
                  <Play className='h-4 w-4 mr-2' />
                  Assign to Reviewer
                </Button>
                <Button
                  variant={selectedOperation === 'reprocess' ? 'default' : 'outline'}
                  size='sm'
                  onClick={() => setSelectedOperation('reprocess')}
                  disabled={selectedCount === 0}
                >
                  <RefreshCw className='h-4 w-4 mr-2' />
                  Reprocess
                </Button>
              </div>
              <Button
                className="w-full"
                onClick={executeBulkOperation}
                disabled={selectedCount === 0 || !selectedOperation}
              >
                Execute {selectedOperation} on {selectedCount} cases
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
