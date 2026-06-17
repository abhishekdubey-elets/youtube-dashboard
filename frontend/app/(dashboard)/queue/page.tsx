'use client';

import * as React from 'react';
import Link from 'next/link';
import { RotateCcw, Ban, FileText, Sparkles } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/status-badge';
import { useCancelVideo, useRetryVideo, useVideos } from '@/lib/queries';
import { useToast } from '@/hooks/use-toast';
import { apiErrorMessage } from '@/lib/api';
import { stageProgress, statusLabel } from '@/lib/utils';
import type { Video, VideoStatus } from '@/lib/types';

function formatDuration(seconds?: number | null): string {
  if (!seconds || seconds <= 0) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const pad = (n: number) => String(n).padStart(2, '0');
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

const ACTIVE: VideoStatus[] = [
  'queued',
  'downloading',
  'extracting',
  'transcribing',
  'summarizing',
  'exporting',
];

export default function QueuePage() {
  const { toast } = useToast();
  const { data, isLoading } = useVideos(
    { page: 1, page_size: 50, sort: '-created_at' },
    { refetchInterval: 5000 }
  );
  const retry = useRetryVideo();
  const cancel = useCancelVideo();

  async function onRetry(v: Video) {
    try {
      await retry.mutateAsync(v.id);
      toast({ variant: 'success', title: 'Retrying', description: v.video_title });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Retry failed', description: apiErrorMessage(err) });
    }
  }

  async function onCancel(v: Video) {
    try {
      await cancel.mutateAsync(v.id);
      toast({ variant: 'warning', title: 'Cancelled', description: v.video_title });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Cancel failed', description: apiErrorMessage(err) });
    }
  }

  const videos = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Processing Queue</h1>
        <p className="text-sm text-muted-foreground">
          Live pipeline status — refreshes every 5 seconds.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : videos.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center text-sm text-muted-foreground">
            Nothing in the queue. Submit a video to get started.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {videos.map((v) => {
            const active = ACTIVE.includes(v.status);
            const progress = stageProgress(v.status);
            const failed = v.status === 'failed';
            return (
              <Card key={v.id}>
                <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={v.thumbnail ?? `https://i.ytimg.com/vi/${v.youtube_video_id}/hqdefault.jpg`}
                    alt=""
                    className="h-20 w-32 shrink-0 rounded-md object-cover"
                  />
                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate font-medium">{v.video_title}</p>
                        <p className="truncate text-xs text-muted-foreground">
                          {v.channel_name ?? '—'} · {formatDuration(v.duration)}
                        </p>
                      </div>
                      <StatusBadge status={v.status} />
                    </div>

                    <div className="space-y-1">
                      <Progress
                        value={progress}
                        indicatorClassName={
                          failed
                            ? 'bg-destructive'
                            : v.status === 'completed'
                              ? 'bg-success'
                              : active
                                ? 'bg-primary bg-[length:40px_40px] animate-progress-stripes bg-gradient-to-r from-primary via-primary/70 to-primary'
                                : 'bg-primary'
                        }
                      />
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{failed ? v.error_message ?? 'Failed' : statusLabel(v.status)}</span>
                        <span>{progress}%</span>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 pt-1">
                      {v.status === 'completed' && (
                        <>
                          <Link href={`/transcripts/${v.id}`}>
                            <Button variant="outline" size="sm">
                              <FileText className="h-4 w-4" /> Transcript
                            </Button>
                          </Link>
                          <Link href={`/summary/${v.id}`}>
                            <Button variant="outline" size="sm">
                              <Sparkles className="h-4 w-4" /> Summary
                            </Button>
                          </Link>
                        </>
                      )}
                      {(failed || v.status === 'cancelled') && (
                        <Button variant="secondary" size="sm" onClick={() => onRetry(v)}>
                          <RotateCcw className="h-4 w-4" /> Retry
                        </Button>
                      )}
                      {active && (
                        <Button variant="ghost" size="sm" onClick={() => onCancel(v)}>
                          <Ban className="h-4 w-4" /> Cancel
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
