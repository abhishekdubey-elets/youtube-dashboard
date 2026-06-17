'use client';

import * as React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import { useToast, type ToastVariant } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

const icons: Record<ToastVariant, React.ReactNode> = {
  default: <Info className="h-5 w-5 text-primary" />,
  success: <CheckCircle2 className="h-5 w-5 text-success" />,
  destructive: <XCircle className="h-5 w-5 text-destructive" />,
  warning: <AlertTriangle className="h-5 w-5 text-warning" />,
};

const accent: Record<ToastVariant, string> = {
  default: 'border-l-primary',
  success: 'border-l-success',
  destructive: 'border-l-destructive',
  warning: 'border-l-warning',
};

export function Toaster() {
  const { toasts, dismiss } = useToast();

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => {
        const variant = t.variant ?? 'default';
        return (
          <div
            key={t.id}
            className={cn(
              'pointer-events-auto flex animate-fade-in items-start gap-3 rounded-lg border border-l-4 bg-popover p-4 text-popover-foreground shadow-lg',
              accent[variant]
            )}
            role="status"
          >
            <div className="mt-0.5 shrink-0">{icons[variant]}</div>
            <div className="flex-1 space-y-1">
              {t.title && <p className="text-sm font-semibold leading-none">{t.title}</p>}
              {t.description && (
                <p className="text-sm text-muted-foreground">{t.description}</p>
              )}
            </div>
            <button
              onClick={() => dismiss(t.id)}
              className="shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
