'use client';

import { useCallback, useRef, useEffect } from 'react';
import { TouchGesture } from '../types/trading';

interface TouchGestureHandlers {
  onTap?: (event: TouchEvent) => void;
  onLongPress?: (event: TouchEvent) => void;
  onSwipeLeft?: (event: TouchEvent) => void;
  onSwipeRight?: (event: TouchEvent) => void;
  onSwipeUp?: (event: TouchEvent) => void;
  onSwipeDown?: (event: TouchEvent) => void;
  onPinch?: (scale: number, event: TouchEvent) => void;
}

interface UseTouchGesturesOptions {
  longPressDelay?: number;
  swipeThreshold?: number;
  pinchThreshold?: number;
  preventDefault?: boolean;
}

export const useTouchGestures = (
  elementRef: React.RefObject<HTMLElement>,
  handlers: TouchGestureHandlers,
  options: UseTouchGesturesOptions = {}
) => {
  const {
    longPressDelay = 500,
    swipeThreshold = 50,
    pinchThreshold = 0.1,
    preventDefault = true
  } = options;

  const touchStartRef = useRef<{
    x: number;
    y: number;
    timestamp: number;
    touches: number;
  } | null>(null);

  const longPressTimerRef = useRef<NodeJS.Timeout>();
  const initialPinchDistanceRef = useRef<number>(0);

  const getTouchDistance = useCallback((touches: TouchList) => {
    if (touches.length < 2) return 0;

    const touch1 = touches[0];
    const touch2 = touches[1];

    return Math.sqrt(
      Math.pow(touch2.clientX - touch1.clientX, 2) +
      Math.pow(touch2.clientY - touch1.clientY, 2)
    );
  }, []);

  const handleTouchStart = useCallback((event: TouchEvent) => {
    if (preventDefault) {
      event.preventDefault();
    }

    const touch = event.touches[0];
    const touchCount = event.touches.length;

    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now(),
      touches: touchCount
    };

    if (touchCount === 1) {
      // Setup long press detection
      longPressTimerRef.current = setTimeout(() => {
        if (handlers.onLongPress) {
          handlers.onLongPress(event);
        }
      }, longPressDelay);
    } else if (touchCount === 2) {
      // Setup pinch detection
      initialPinchDistanceRef.current = getTouchDistance(event.touches);
    }
  }, [handlers, longPressDelay, preventDefault, getTouchDistance]);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (preventDefault) {
      event.preventDefault();
    }

    if (!touchStartRef.current) return;

    const touchCount = event.touches.length;

    if (touchCount === 2 && initialPinchDistanceRef.current > 0) {
      // Handle pinch gesture
      const currentDistance = getTouchDistance(event.touches);
      const scale = currentDistance / initialPinchDistanceRef.current;

      if (Math.abs(scale - 1) > pinchThreshold && handlers.onPinch) {
        handlers.onPinch(scale, event);
      }
    }

    // Cancel long press if finger moves too much
    if (longPressTimerRef.current) {
      const touch = event.touches[0];
      const deltaX = Math.abs(touch.clientX - touchStartRef.current.x);
      const deltaY = Math.abs(touch.clientY - touchStartRef.current.y);

      if (deltaX > 10 || deltaY > 10) {
        clearTimeout(longPressTimerRef.current);
        longPressTimerRef.current = undefined;
      }
    }
  }, [preventDefault, getTouchDistance, pinchThreshold, handlers]);

  const handleTouchEnd = useCallback((event: TouchEvent) => {
    if (preventDefault) {
      event.preventDefault();
    }

    if (!touchStartRef.current) return;

    // Clear long press timer
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = undefined;
    }

    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - touchStartRef.current.x;
    const deltaY = touch.clientY - touchStartRef.current.y;
    const deltaTime = Date.now() - touchStartRef.current.timestamp;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // Determine gesture type
    if (distance < 10 && deltaTime < 300) {
      // Tap gesture
      if (handlers.onTap) {
        handlers.onTap(event);
      }
    } else if (distance > swipeThreshold && deltaTime < 500) {
      // Swipe gesture
      const absX = Math.abs(deltaX);
      const absY = Math.abs(deltaY);

      if (absX > absY) {
        // Horizontal swipe
        if (deltaX > 0 && handlers.onSwipeRight) {
          handlers.onSwipeRight(event);
        } else if (deltaX < 0 && handlers.onSwipeLeft) {
          handlers.onSwipeLeft(event);
        }
      } else {
        // Vertical swipe
        if (deltaY > 0 && handlers.onSwipeDown) {
          handlers.onSwipeDown(event);
        } else if (deltaY < 0 && handlers.onSwipeUp) {
          handlers.onSwipeUp(event);
        }
      }
    }

    touchStartRef.current = null;
    initialPinchDistanceRef.current = 0;
  }, [preventDefault, swipeThreshold, handlers]);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd, { passive: false });

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);

      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
      }
    };
  }, [elementRef, handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    isActive: touchStartRef.current !== null
  };
};