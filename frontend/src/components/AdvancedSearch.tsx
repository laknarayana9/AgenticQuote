'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Search, Filter, X, ChevronDown, ChevronUp } from 'lucide-react'

interface SearchFilter {
  id: string
  field: string
  operator: string
  value: string
}

export function AdvancedSearch() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState<SearchFilter[]>([
    { id: 'filter-1', field: 'status', operator: 'equals', value: 'pending' }
  ])
  const [expandedFilters, setExpandedFilters] = useState(true)

  const addFilter = () => {
    const newFilter: SearchFilter = {
      id: `filter-${filters.length + 1}`,
      field: 'risk_level',
      operator: 'equals',
      value: ''
    }
    setFilters([...filters, newFilter])
  }

  const removeFilter = (filterId: string) => {
    setFilters(filters.filter(f => f.id !== filterId))
  }

  const updateFilter = (filterId: string, updates: Partial<SearchFilter>) => {
    setFilters(filters.map(f => 
      f.id === filterId ? { ...f, ...updates } : f
    ))
  }

  const clearAllFilters = () => {
    setFilters([])
    setSearchQuery('')
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Advanced Search</CardTitle>
            <CardDescription>Search and filter cases</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={clearAllFilters}>
            <X className="h-4 w-4 mr-2" />
            Clear All
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search cases by ID, address, or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800"
            />
          </div>

          <div className="border-t pt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpandedFilters(!expandedFilters)}
              className="w-full justify-between"
            >
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Filters ({filters.length})
              </div>
              {expandedFilters ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>

            {expandedFilters && (
              <div className="mt-4 space-y-3">
                {filters.map((filter) => (
                  <div key={filter.id} className="flex items-center gap-2">
                    <select
                      value={filter.field}
                      onChange={(e) => updateFilter(filter.id, { field: e.target.value })}
                      className="px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-sm"
                    >
                      <option value="status">Status</option>
                      <option value="risk_level">Risk Level</option>
                      <option value="agent">Agent</option>
                      <option value="date_created">Date Created</option>
                      <option value="property_address">Property Address</option>
                    </select>

                    <select
                      value={filter.operator}
                      onChange={(e) => updateFilter(filter.id, { operator: e.target.value })}
                      className="px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-sm"
                    >
                      <option value="equals">Equals</option>
                      <option value="not_equals">Not Equals</option>
                      <option value="contains">Contains</option>
                      <option value="greater_than">Greater Than</option>
                      <option value="less_than">Less Than</option>
                    </select>

                    <input
                      type="text"
                      value={filter.value}
                      onChange={(e) => updateFilter(filter.id, { value: e.target.value })}
                      placeholder="Value"
                      className="flex-1 px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-800 text-sm"
                    />

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFilter(filter.id)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}

                <Button onClick={addFilter} size="sm" variant="outline" className="w-full">
                  <Filter className="h-4 w-4 mr-2" />
                  Add Filter
                </Button>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <Button className="flex-1">Search</Button>
            <Button variant="outline">Export Results</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
