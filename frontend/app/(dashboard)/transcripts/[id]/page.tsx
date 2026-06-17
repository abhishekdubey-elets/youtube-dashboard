'use client';

import * as React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Copy, Download, Search, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { useTranscript, useVideo } from '@/lib/queries';
import { downloadTextFile } from '@/lib/utils';

function formatTs(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) return '';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

function highlight(text: string, query: string): React.ReactNode {
  if (!query.trim()) return text;
  const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase() ? (
      <mark key={i} className="highlight-match">
        {part}
      </mark>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    )
  );
}

export default function TranscriptPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { toast } = useToast();
  const [query, setQuery] = React.useState('');

  const { data: video } = useVideo(id);
  const { data: transcript, isLoading, isError } = useTranscript(id);

  function onCopy() {
    if (!transcript) return;
    navigator.clipboard.writeText(transcript.full_transcript);
    toast({ variant: 'success', title: 'Copied', description: 'Transcript copied to clipboard.' });
  }

  function onDownload() {
    if (!transcript) return;
    const name = (video?.video_title ?? `transcript-${id}`).replace(/[^a-z0-9]+/gi, '_');
    downloadTextFile(`${name}.txt`, transcript.full_transcript);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Link href="/queue">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              {video?.video_title ?? 'Transcript'}
            </h1>
            <p className="text-sm text-muted-foreground">{video?.channel_name}</p>
          </div>
        </div>
        <Link href={`/summary/${id}`}>
          <Button variant="outline">
            <Sparkles className="h-4 w-4" /> View AI Summary
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2 space-y-4">
          {video?.youtube_video_id && (
            <div className="aspect-video overflow-hidden rounded-xl border border-border">
              <iframe
                className="h-full w-full"
                src={`https://www.youtube.com/embed/${video.youtube_video_id}`}
                title={video.video_title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          )}
          <Card>
            <CardContent className="flex items-center justify-around p-4 text-center">
              <div>
                <p className="text-2xl font-bold">{transcript?.word_count ?? 0}</p>
                <p className="text-xs text-muted-foreground">Words</p>
              </div>
              <div>
                <p className="text-2xl font-bold uppercase">{transcript?.language ?? '—'}</p>
                <p className="text-xs text-muted-foreground">Language</p>
              </div>
              <div>
                <Badge variant="secondary">{transcript?.provider ?? 'n/a'}</Badge>
                <p className="mt-1 text-xs text-muted-foreground">Engine</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="lg:col-span-3">
          <CardHeader className="gap-3">
            <CardTitle className="text-base">Transcript</CardTitle>
            <div className="flex flex-wrap gap-2">
              <div className="relative flex-1 min-w-[180px]">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search transcript…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <Button variant="outline" size="icon" onClick={onCopy} aria-label="Copy">
                <Copy className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" onClick={onDownload} aria-label="Download">
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-4 w-full" />
                ))}
              </div>
            ) : isError ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Transcript not available yet.
              </p>
            ) : transcript?.segments && transcript.segments.length > 0 ? (
              <div className="max-h-[60vh] space-y-3 overflow-y-auto scrollbar-thin pr-2">
                {transcript.segments.map((seg, i) => (
                  <div key={i} className="flex gap-3 text-sm">
                    <span className="shrink-0 select-none font-mono text-xs text-muted-foreground">
                      {formatTs(seg.start)}
                    </span>
                    <p className="leading-relaxed">
                      {seg.speaker !== null && seg.speaker !== undefined && (
                        <span className="mr-1 font-semibold text-primary">
                          S{String(seg.speaker)}:
                        </span>
                      )}
                      {highlight(seg.text, query)}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="max-h-[60vh] overflow-y-auto scrollbar-thin whitespace-pre-wrap text-sm leading-relaxed">
                {highlight(transcript?.full_transcript ?? '', query)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
