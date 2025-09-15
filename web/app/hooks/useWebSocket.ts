'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { WebSocketMessage } from '../types/trading';

interface UseWebSocketProps {
  url: string;
  options?: {
    autoConnect?: boolean;
    reconnectAttempts?: number;
    reconnectDelay?: number;
  };
}

interface UseWebSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  error: string | null;
  sendMessage: (type: string, data: any) => void;
  subscribe: (event: string, callback: (data: any) => void) => () => void;
  reconnect: () => void;
}

export const useWebSocket = ({
  url,
  options = {}
}: UseWebSocketProps): UseWebSocketReturn => {
  const {
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectDelay = 3000
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    try {
      const socket = io(url, {
        transports: ['websocket', 'polling'],
        forceNew: true,
        timeout: 10000,
      });

      socket.on('connect', () => {
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        console.log('WebSocket connected');
      });

      socket.on('disconnect', (reason) => {
        setIsConnected(false);
        console.log('WebSocket disconnected:', reason);

        if (reason === 'io server disconnect') {
          // Server disconnected, try to reconnect
          attemptReconnect();
        }
      });

      socket.on('connect_error', (err) => {
        setError(err.message);
        setIsConnected(false);
        console.error('WebSocket connection error:', err);
        attemptReconnect();
      });

      socketRef.current = socket;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      attemptReconnect();
    }
  }, [url]);

  const attemptReconnect = useCallback(() => {
    if (reconnectCountRef.current >= reconnectAttempts) {
      setError('Max reconnection attempts reached');
      return;
    }

    reconnectCountRef.current++;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(`Reconnection attempt ${reconnectCountRef.current}/${reconnectAttempts}`);
      connect();
    }, reconnectDelay);
  }, [connect, reconnectAttempts, reconnectDelay]);

  const sendMessage = useCallback((type: string, data: any) => {
    if (socketRef.current?.connected) {
      const message: WebSocketMessage = {
        type: type as any,
        data,
        timestamp: Date.now()
      };
      socketRef.current.emit('message', message);
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }, []);

  const subscribe = useCallback((event: string, callback: (data: any) => void) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback);

      return () => {
        if (socketRef.current) {
          socketRef.current.off(event, callback);
        }
      };
    }

    return () => {};
  }, []);

  const reconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
    reconnectCountRef.current = 0;
    connect();
  }, [connect]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [autoConnect, connect]);

  return {
    socket: socketRef.current,
    isConnected,
    error,
    sendMessage,
    subscribe,
    reconnect
  };
};