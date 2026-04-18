import * as React from "react"
import { cn } from "@/utils"

const Tabs = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { defaultValue?: string }
>(({ className, defaultValue, ...props }, ref) => {
  const [activeTab, setActiveTab] = React.useState(defaultValue || "overview")

  return (
    <div ref={ref} className={cn("w-full", className)} {...props}>
      <TabsContext.Provider value={{ activeTab, setActiveTab }}>
        {React.Children.map(props.children, (child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, { activeTab, setActiveTab } as any)
          }
          return child
        })}
      </TabsContext.Provider>
    </div>
  )
})
Tabs.displayName = "Tabs"

const TabsContext = React.createContext<{
  activeTab: string
  setActiveTab: (tab: string) => void
}>({
  activeTab: "overview",
  setActiveTab: () => {},
})

const TabsList = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { activeTab?: string; setActiveTab?: (tab: string) => void }
>(({ className, children, activeTab, setActiveTab }, ref) => {
  return (
    <TabsContext.Consumer>
      {({ activeTab: contextActiveTab, setActiveTab: contextSetActiveTab }) => (
        <div
          ref={ref}
          className={cn(
            "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
            className
          )}
        >
          {React.Children.map(children, (child) => {
            if (React.isValidElement(child)) {
              return React.cloneElement(child, {
                activeTab: activeTab || contextActiveTab,
                setActiveTab: setActiveTab || contextSetActiveTab,
              } as any)
            }
            return child
          })}
        </div>
      )}
    </TabsContext.Consumer>
  )
})
TabsList.displayName = "TabsList"

const TabsTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    value: string
    activeTab?: string
    setActiveTab?: (tab: string) => void
  }
>(({ className, children, value, activeTab, setActiveTab, ...props }, ref) => {
  const isActive = activeTab === value

  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-background text-foreground shadow-sm"
          : "text-muted-foreground hover:bg-background/50 hover:text-foreground",
        className
      )}
      onClick={() => setActiveTab?.(value)}
      {...props}
    >
      {children}
    </button>
  )
})
TabsTrigger.displayName = "TabsTrigger"

const TabsContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value: string; activeTab?: string }
>(({ className, children, value, activeTab, ...props }, ref) => {
  const isActive = activeTab === value

  if (!isActive) return null

  return (
    <div
      ref={ref}
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
})
TabsContent.displayName = "TabsContent"

export { Tabs, TabsList, TabsTrigger, TabsContent }
