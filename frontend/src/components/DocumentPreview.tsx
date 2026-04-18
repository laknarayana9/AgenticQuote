'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Download, ZoomIn, ZoomOut, MessageSquare, X } from 'lucide-react'

interface Annotation {
  id: string
  x: number
  y: number
  text: string
  author: string
  timestamp: number
}

export function DocumentPreview() {
  const [zoom, setZoom] = useState(100)
  const [annotations, setAnnotations] = useState<Annotation[]>([
    { id: '1', x: 100, y: 150, text: 'Missing flood risk score', author: 'John D.', timestamp: Date.now() },
    { id: '2', x: 300, y: 250, text: 'Verify property address', author: 'Sarah M.', timestamp: Date.now() },
  ])
  const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | null>(null)
  const [newAnnotationText, setNewAnnotationText] = useState('')

  const zoomIn = () => setZoom(Math.min(zoom + 10, 200))
  const zoomOut = () => setZoom(Math.max(zoom - 10, 50))

  const addAnnotation = (x: number, y: number) => {
    if (newAnnotationText.trim()) {
      const newAnnotation: Annotation = {
        id: `${Date.now()}`,
        x,
        y,
        text: newAnnotationText,
        author: 'Current User',
        timestamp: Date.now()
      }
      setAnnotations([...annotations, newAnnotation])
      setNewAnnotationText('')
    }
  }

  const removeAnnotation = (annotationId: string) => {
    setAnnotations(annotations.filter(a => a.id !== annotationId))
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Document Preview</CardTitle>
            <CardDescription>Preview and annotate documents</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={zoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="text-sm text-slate-600 dark:text-slate-400">
              {zoom}%
            </span>
            <Button variant="outline" size="sm" onClick={zoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="relative bg-white dark:bg-slate-800 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-lg min-h-[400px]">
            <div
              className="absolute inset-0 overflow-auto p-8"
              style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top left' }}
            >
              <div className="bg-slate-50 dark:bg-slate-900 p-8 rounded shadow-sm">
                <div className="text-center mb-6">
                  <FileText className="h-16 w-16 mx-auto text-slate-400 mb-4" />
                  <p className="text-lg font-medium">Property Insurance Application</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Case #1001</p>
                </div>
                <div className="space-y-4">
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
                  <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                </div>
              </div>

              {annotations.map((annotation) => (
                <div
                  key={annotation.id}
                  className="absolute bg-yellow-100 dark:bg-yellow-900 border-2 border-yellow-400 dark:border-yellow-600 rounded p-2 cursor-pointer max-w-xs"
                  style={{ left: annotation.x, top: annotation.y }}
                  onClick={() => setSelectedAnnotation(annotation)}
                >
                  <div className="flex items-center justify-between gap-2">
                    <MessageSquare className="h-3 w-3 text-yellow-600 dark:text-yellow-400" />
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0"
                      onClick={(e) => {
                        e.stopPropagation()
                        removeAnnotation(annotation.id)
                      }}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                  <p className="text-xs mt-1">{annotation.text}</p>
                  <p className="text-[10px] text-slate-600 dark:text-slate-400 mt-1">
                    {annotation.author}
                  </p>
                </div>
              ))}
            </div>

            <div className="absolute bottom-4 left-4 right-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 shadow-lg">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add annotation..."
                  value={newAnnotationText}
                  onChange={(e) => setNewAnnotationText(e.target.value)}
                  className="flex-1 px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-sm"
                />
                <Button
                  size="sm"
                  onClick={() => addAnnotation(50, 50)}
                  disabled={!newAnnotationText.trim()}
                >
                  Add
                </Button>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Annotations ({annotations.length})</p>
            <div className="space-y-2">
              {annotations.map((annotation) => (
                <div
                  key={annotation.id}
                  className="flex items-start gap-3 p-3 rounded-lg border bg-slate-50 dark:bg-slate-800"
                >
                  <MessageSquare className="h-4 w-4 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{annotation.text}</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {annotation.author} • {new Date(annotation.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeAnnotation(annotation.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
