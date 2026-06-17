import { Badge, type BadgeProps } from '@/components/ui/badge';
import type { VideoStatus } from '@/lib/types';
import { statusLabel } from '@/lib/utils';

const VARIANT: Record<VideoStatus, BadgeProps['variant']> = {
  queued: 'secondary',
  downloading: 'warning',
  extracting: 'warning',
  transcribing: 'warning',
  summarizing: 'warning',
  exporting: 'warning',
  completed: 'success',
  failed: 'destructive',
  cancelled: 'outline',
};

export function StatusBadge({ status }: { status: VideoStatus }) {
  return <Badge variant={VARIANT[status] ?? 'secondary'}>{statusLabel(status)}</Badge>;
}
