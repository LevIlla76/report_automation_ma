"use client";

import { useState, useEffect, useCallback } from "react";
import { Minus, Square, X, Maximize2, Download, RefreshCw, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

/**
 * TitleBar — Discord-style custom frameless window title bar.
 * Communicates with Electron main process via window.electronAPI (preload bridge).
 * Gracefully degrades in browser (no electronAPI).
 */
export default function TitleBar() {
  const [isMaximized, setIsMaximized] = useState(false);
  const [updaterState, setUpdaterState] = useState(null);
  // null | 'checking' | 'available' | 'downloading' | 'downloaded' | 'error'
  const [updateInfo, setUpdateInfo] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [showUpdateBanner, setShowUpdateBanner] = useState(false);

  const api = typeof window !== "undefined" ? window.electronAPI : null;

  // ── Window state sync ─────────────────────────────────────
  useEffect(() => {
    if (!api) return;
    api.isMaximized().then(setIsMaximized);
  }, [api]);

  // ── Updater events ────────────────────────────────────────
  useEffect(() => {
    if (!api) return;

    const cleanups = [
      api.onUpdaterEvent("updater:checking", () => {
        setUpdaterState("checking");
      }),
      api.onUpdaterEvent("updater:available", (info) => {
        setUpdaterState("available");
        setUpdateInfo(info);
        setShowUpdateBanner(true);
      }),
      api.onUpdaterEvent("updater:not-available", () => {
        setUpdaterState(null);
      }),
      api.onUpdaterEvent("updater:progress", (progress) => {
        setUpdaterState("downloading");
        setDownloadProgress(progress.percent);
        setShowUpdateBanner(true);
      }),
      api.onUpdaterEvent("updater:downloaded", (info) => {
        setUpdaterState("downloaded");
        setUpdateInfo(info);
        setShowUpdateBanner(true);
      }),
      api.onUpdaterEvent("updater:error", () => {
        setUpdaterState("error");
      }),
    ];

    return () => cleanups.forEach((fn) => fn && fn());
  }, [api]);

  // ── Window controls ───────────────────────────────────────
  const handleMinimize = useCallback(() => api?.minimize(), [api]);
  const handleMaximize = useCallback(() => {
    api?.maximize();
    setIsMaximized((prev) => !prev);
  }, [api]);
  const handleClose = useCallback(() => api?.close(), [api]);
  const handleInstall = useCallback(() => api?.installUpdate(), [api]);

  // ── Update banner content ─────────────────────────────────
  const renderUpdaterBadge = () => {
    if (!updaterState || updaterState === "checking") return null;

    if (updaterState === "available") {
      return (
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-500/20 border border-blue-500/40 text-blue-400 text-xs">
          <Download className="w-3 h-3 animate-bounce" />
          <span>v{updateInfo?.version} downloading…</span>
        </div>
      );
    }
    if (updaterState === "downloading") {
      return (
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-500/20 border border-blue-500/40 text-blue-400 text-xs">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>Updating {downloadProgress}%</span>
        </div>
      );
    }
    if (updaterState === "downloaded") {
      return (
        <button
          onClick={handleInstall}
          className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-green-500/20 border border-green-500/40 text-green-400 text-xs hover:bg-green-500/30 transition-colors"
        >
          <CheckCircle className="w-3 h-3" />
          <span>v{updateInfo?.version} ready — Click to restart & install</span>
        </button>
      );
    }
    if (updaterState === "error") {
      return (
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-500/15 border border-red-500/30 text-red-400 text-xs">
          <AlertCircle className="w-3 h-3" />
          <span>Update failed</span>
        </div>
      );
    }
    return null;
  };

  return (
    <div
      className="select-none flex-shrink-0"
      style={{ WebkitAppRegion: "drag", height: "40px" }}
    >
      {/* Main title bar row */}
      <div className="flex items-center h-full px-3 gap-3 bg-[#1e1f22] border-b border-white/5">
        {/* App icon + name */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="w-5 h-5 rounded bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center text-[11px]">
            📊
          </div>
          <span className="text-[13px] font-semibold text-white/90 tracking-tight">
            OCR Report Automation
          </span>
        </div>

        {/* Separator */}
        <div className="w-px h-4 bg-white/10 shrink-0" />

        {/* Updater badge (non-draggable) */}
        <div style={{ WebkitAppRegion: "no-drag" }}>
          {renderUpdaterBadge()}
        </div>

        {/* Spacer — draggable area */}
        <div className="flex-1" />

        {/* Window controls (no-drag) */}
        <div
          className="flex items-center"
          style={{ WebkitAppRegion: "no-drag" }}
        >
          <button
            onClick={handleMinimize}
            title="Minimize"
            className="w-11 h-10 flex items-center justify-center text-[#b5bac1] hover:text-white hover:bg-white/8 transition-colors"
          >
            <Minus className="w-4 h-4" />
          </button>
          <button
            onClick={handleMaximize}
            title={isMaximized ? "Restore" : "Maximize"}
            className="w-11 h-10 flex items-center justify-center text-[#b5bac1] hover:text-white hover:bg-white/8 transition-colors"
          >
            {isMaximized ? (
              <Square className="w-3.5 h-3.5" />
            ) : (
              <Maximize2 className="w-3.5 h-3.5" />
            )}
          </button>
          <button
            onClick={handleClose}
            title="Close"
            className="w-11 h-10 flex items-center justify-center text-[#b5bac1] hover:text-white hover:bg-red-600 transition-colors rounded-tr"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Downloading progress strip */}
      <AnimatePresence>
        {updaterState === "downloading" && (
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: downloadProgress / 100 }}
            exit={{ opacity: 0 }}
            className="h-[2px] bg-gradient-to-r from-indigo-500 to-blue-400 origin-left"
            style={{ transformOrigin: "left center" }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
