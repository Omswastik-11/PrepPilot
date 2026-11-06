"use client";

import { useToastStore } from "@/lib/store";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

export function Toast() {
  const { message, type, hide } = useToastStore();

  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          className="fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl border bg-[var(--sidebar-background)] text-sm font-medium"
        >
          {type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
          {type === 'error' && <AlertCircle className="w-5 h-5 text-red-500" />}
          {type === 'info' && <Info className="w-5 h-5 text-blue-500" />}
          
          <span className="text-[var(--foreground)] pr-4">{message}</span>
          
          <button 
            onClick={hide}
            className="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors p-1 -mr-2"
          >
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
