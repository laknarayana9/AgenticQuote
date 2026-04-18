'use client'

import { useState } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, GripVertical, Trash2 } from 'lucide-react'

interface WorkflowNode {
  id: string
  type: 'input' | 'agent' | 'decision' | 'hitl' | 'output'
  name: string
  config: any
}

interface WorkflowConnection {
  id: string
  from: string
  to: string
  condition?: string
}

export function WorkflowDesigner() {
  const [nodes, setNodes] = useState<WorkflowNode[]>([
    { id: 'node-1', type: 'input', name: 'Case Input', config: {} },
    { id: 'node-2', type: 'agent', name: 'Property Agent', config: {} },
    { id: 'node-3', type: 'agent', name: 'Hazard Agent', config: {} },
    { id: 'node-4', type: 'decision', name: 'Risk Decision', config: {} },
    { id: 'node-5', type: 'hitl', name: 'Human Review', config: {} },
    { id: 'node-6', type: 'output', name: 'Final Decision', config: {} },
  ])

  const [connections, setConnections] = useState<WorkflowConnection[]>([
    { id: 'conn-1', from: 'node-1', to: 'node-2' },
    { id: 'conn-2', from: 'node-2', to: 'node-3' },
    { id: 'conn-3', from: 'node-3', to: 'node-4' },
    { id: 'conn-4', from: 'node-4', to: 'node-5', condition: 'needs_review' },
    { id: 'conn-5', from: 'node-4', to: 'node-6', condition: 'auto_approve' },
    { id: 'conn-6', from: 'node-5', to: 'node-6' },
  ])

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return

    const items = Array.from(nodes)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    setNodes(items)
  }

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'input':
        return 'bg-blue-100 dark:bg-blue-900 border-blue-300 dark:border-blue-700'
      case 'agent':
        return 'bg-green-100 dark:bg-green-900 border-green-300 dark:border-green-700'
      case 'decision':
        return 'bg-yellow-100 dark:bg-yellow-900 border-yellow-300 dark:border-yellow-700'
      case 'hitl':
        return 'bg-purple-100 dark:bg-purple-900 border-purple-300 dark:border-purple-700'
      case 'output':
        return 'bg-red-100 dark:bg-red-900 border-red-300 dark:border-red-700'
      default:
        return 'bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700'
    }
  }

  const addNode = () => {
    const newNode: WorkflowNode = {
      id: `node-${nodes.length + 1}`,
      type: 'agent',
      name: `New Node ${nodes.length + 1}`,
      config: {}
    }
    setNodes([...nodes, newNode])
  }

  const removeNode = (nodeId: string) => {
    setNodes(nodes.filter(n => n.id !== nodeId))
    setConnections(connections.filter(c => c.from !== nodeId && c.to !== nodeId))
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Workflow Designer</CardTitle>
            <CardDescription>Drag and drop to design underwriting workflows</CardDescription>
          </div>
          <Button onClick={addNode} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Node
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <DragDropContext onDragEnd={onDragEnd}>
          <Droppable droppableId="workflow">
            {(provided) => (
              <div
                {...provided.droppableProps}
                ref={provided.innerRef}
                className="space-y-3"
              >
                {nodes.map((node, index) => (
                  <Draggable key={node.id} draggableId={node.id} index={index}>
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        className="flex items-center gap-3"
                      >
                        <div {...provided.dragHandleProps}>
                          <GripVertical className="h-4 w-4 text-slate-400" />
                        </div>
                        <div
                          className={`flex-1 p-4 rounded-lg border-2 ${getNodeColor(node.type)}`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">{node.name}</p>
                              <p className="text-xs text-slate-600 dark:text-slate-400 capitalize">
                                {node.type}
                              </p>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeNode(node.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>

        <div className="mt-6 pt-6 border-t">
          <h4 className="text-sm font-medium mb-3">Workflow Connections</h4>
          <div className="space-y-2">
            {connections.map((conn) => {
              const fromNode = nodes.find(n => n.id === conn.from)
              const toNode = nodes.find(n => n.id === conn.to)
              return (
                <div key={conn.id} className="flex items-center gap-2 text-sm">
                  <span className="font-medium">{fromNode?.name}</span>
                  <span className="text-slate-400">→</span>
                  <span className="font-medium">{toNode?.name}</span>
                  {conn.condition && (
                    <span className="text-xs text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                      {conn.condition}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
