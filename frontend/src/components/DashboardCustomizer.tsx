'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Eye, EyeOff, Plus, Trash2, GripVertical } from 'lucide-react'

interface DashboardWidget {
  id: string
  name: string
  type: 'stats' | 'chart' | 'list' | 'table'
  visible: boolean
  position: { x: number; y: number }
  size: { width: number; height: number }
}

export function DashboardCustomizer() {
  const [widgets, setWidgets] = useState<DashboardWidget[]>([
    { id: 'widget-1', name: 'Total Cases', type: 'stats', visible: true, position: { x: 0, y: 0 }, size: { width: 1, height: 1 } },
    { id: 'widget-2', name: 'Case Volume Chart', type: 'chart', visible: true, position: { x: 1, y: 0 }, size: { width: 2, height: 1 } },
    { id: 'widget-3', name: 'Recent Activity', type: 'list', visible: true, position: { x: 0, y: 1 }, size: { width: 1, height: 2 } },
    { id: 'widget-4', name: 'System Health', type: 'stats', visible: true, position: { x: 1, y: 1 }, size: { width: 1, height: 1 } },
    { id: 'widget-5', name: 'Risk Distribution', type: 'chart', visible: true, position: { x: 2, y: 1 }, size: { width: 1, height: 1 } },
  ])

  const toggleVisibility = (widgetId: string) => {
    setWidgets(widgets.map(w => 
      w.id === widgetId ? { ...w, visible: !w.visible } : w
    ))
  }

  const removeWidget = (widgetId: string) => {
    setWidgets(widgets.filter(w => w.id !== widgetId))
  }

  const addWidget = () => {
    const newWidget: DashboardWidget = {
      id: `widget-${widgets.length + 1}`,
      name: `New Widget ${widgets.length + 1}`,
      type: 'stats',
      visible: true,
      position: { x: 0, y: 0 },
      size: { width: 1, height: 1 }
    }
    setWidgets([...widgets, newWidget])
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Dashboard Customizer</CardTitle>
            <CardDescription>Customize your dashboard layout</CardDescription>
          </div>
          <Button onClick={addWidget} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Widget
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          {widgets.map((widget) => (
            <div
              key={widget.id}
              className={`p-4 rounded-lg border-2 ${
                widget.visible
                  ? 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700'
                  : 'bg-slate-100 dark:bg-slate-900 border-slate-200 dark:border-slate-700 opacity-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <GripVertical className="h-4 w-4 text-slate-400" />
                  <span className="font-medium">{widget.name}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleVisibility(widget.id)}
                  >
                    {widget.visible ? (
                      <Eye className="h-4 w-4" />
                    ) : (
                      <EyeOff className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeWidget(widget.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="text-xs text-slate-600 dark:text-slate-400">
                Type: {widget.type}
              </div>
              <div className="text-xs text-slate-600 dark:text-slate-400">
                Size: {widget.size.width}x{widget.size.height}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-6 border-t">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Settings className="h-4 w-4 text-slate-400" />
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {widgets.filter(w => w.visible).length} widgets visible
              </span>
            </div>
            <Button variant="outline" size="sm">
              Reset to Default
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
