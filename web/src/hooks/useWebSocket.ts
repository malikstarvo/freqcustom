import { useEffect, useRef, useState, useCallback } from "react";

type WSMessage = {
  type: string;
  data: unknown;
};

export function useWebSocket(wsUrl: string = "/api/v1/message/ws") {
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [readyState, setReadyState] = useState<number>(
    typeof WebSocket !== "undefined" ? WebSocket.CONNECTING : 0
  );
  const [subscriptions, setSubscriptions] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | null>(null);
  const retriesRef = useRef(0);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    let wsHost = window.location.host;
    let protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    let wsPath = wsUrl;

    const apiEnv = process.env.NEXT_PUBLIC_API_URL;
    if (apiEnv && apiEnv.startsWith("http")) {
      try {
        const urlObj = new URL(apiEnv);
        wsHost = urlObj.host;
        protocol = urlObj.protocol === "https:" ? "wss:" : "ws:";
        const basePath = urlObj.pathname.replace(/\/$/, "");
        if (wsUrl.startsWith("/api/v1/")) {
          wsPath = `${basePath}${wsUrl.substring(7)}`;
        } else {
          wsPath = `${basePath}${wsUrl}`;
        }
      } catch (e) {
        console.error("Failed to parse NEXT_PUBLIC_API_URL for WebSocket:", e);
      }
    }

    const token = localStorage.getItem("freqtrade-token");
    const tokenParam = token ? `?token=${token}` : "";
    const url = `${protocol}//${wsHost}${wsPath}${tokenParam}`;

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
      if (!mountedRef.current) return;
      const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 30000);
      retriesRef.current++;
      reconnectRef.current = window.setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [wsUrl, subscriptions]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (reconnectRef.current !== null) clearTimeout(reconnectRef.current);
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
