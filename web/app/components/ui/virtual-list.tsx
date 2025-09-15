'use client'

import { memo, useMemo, useCallback, useState, useEffect, useRef } from 'react'

interface VirtualListProps<T> {
  items: T[]
  itemHeight: number
  containerHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
  overscan?: number
  className?: string
  onEndReached?: () => void
  endReachedThreshold?: number
}

function VirtualList<T extends { id: string | number }>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  className = '',
  onEndReached,
  endReachedThreshold = 0.8
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  // Calculate visible range
  const { startIndex, endIndex, offsetY } = useMemo(() => {
    const start = Math.floor(scrollTop / itemHeight)
    const visibleCount = Math.ceil(containerHeight / itemHeight)

    const startIndex = Math.max(0, start - overscan)
    const endIndex = Math.min(items.length - 1, start + visibleCount + overscan)
    const offsetY = startIndex * itemHeight

    return { startIndex, endIndex, offsetY }
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length])

  // Get visible items
  const visibleItems = useMemo(() => {
    return items.slice(startIndex, endIndex + 1)
  }, [items, startIndex, endIndex])

  // Handle scroll with throttling for better performance
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop
    setScrollTop(newScrollTop)

    // Check if we've reached the end
    if (onEndReached) {
      const { scrollHeight, clientHeight } = e.currentTarget
      const scrollPercentage = (newScrollTop + clientHeight) / scrollHeight

      if (scrollPercentage >= endReachedThreshold) {
        onEndReached()
      }
    }
  }, [onEndReached, endReachedThreshold])

  // Scroll event throttling
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    let ticking = false
    const handleScrollThrottled = (e: Event) => {
      if (!ticking) {
        requestAnimationFrame(() => {
          handleScroll(e as any)
          ticking = false
        })
        ticking = true
      }
    }

    container.addEventListener('scroll', handleScrollThrottled, { passive: true })
    return () => container.removeEventListener('scroll', handleScrollThrottled)
  }, [handleScroll])

  const totalHeight = items.length * itemHeight

  return (
    <div
      ref={containerRef}
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, index) => (
            <div
              key={item.id}
              style={{ height: itemHeight }}
              className="flex-shrink-0"
            >
              {renderItem(item, startIndex + index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default memo(VirtualList) as typeof VirtualList