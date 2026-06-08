import { useEffect, useRef, useState, useCallback } from "react";

type WSMessage = {
  type: string;
  data: unknown;
};

export function useWebSocket(wsUrl: string = "/api/v1/message/ws") {
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const [subscriptions, setSubscriptions] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retriesRef = useRef(0);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}${wsUrl}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setReadyState(WebSocket.OPEN);
      retriesRef.current = 0;
      if (subscriptions.length > 0) {
        ws.send(JSON.stringify({ type: "subscribe", data: subscriptions }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        setLastMessage(msg);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setReadyState(WebSocket.CLOSED);
      const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000);
      retriesRef.current++;
      reconnectRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [wsUrl, subscriptions]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const subscribe = useCallback((types: string[]) => {
    setSubscriptions(types);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "subscribe", data: types }));
    }
  }, []);

  return { lastMessage, readyState, subscribe };
}
