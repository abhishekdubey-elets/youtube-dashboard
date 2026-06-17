'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, ListVideo, PlayCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { useProcessPlaylist, useProcessVideo, useValidateUrl } from '@/lib/queries';
import { apiErrorMessage } from '@/lib/api';
import type { ValidateResult } from '@/lib/types';

function looksLikePlaylist(url: string): boolean {
  return url.includes('list=') && !url.includes('watch?v=');
}

export default function SubmitPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [url, setUrl] = React.useState('');
  const [preview, setPreview] = React.useState<ValidateResult | null>(null);

  const validate = useValidateUrl();
  const processVideo = useProcessVideo();
  const processPlaylist = useProcessPlaylist();

  async function onValidate() {
    if (!url.trim()) return;
    setPreview(null);
    try {
      const res = await validate.mutateAsync(url.trim());
      setPreview(res);
      if (!res.valid) {
        toast({ variant: 'warning', title: 'Invalid URL', description: res.message });
      }
    } catch (err) {
      toast({ variant: 'destructive', title: 'Validation failed', description: apiErrorMessage(err) });
    }
  }

  async function onStart() {
    if (!url.trim()) return;
    const isPlaylist = preview?.type === 'playlist' || looksLikePlaylist(url);
    try {
      if (isPlaylist) {
        const res = await processPlaylist.mutateAsync(url.trim());
        toast({
          variant: 'success',
          title: 'Playlist queued',
          description: `${res.queued} videos added to the pipeline.`,
        });
      } else {
        await processVideo.mutateAsync(url.trim());
        toast({ variant: 'success', title: 'Video queued', description: 'Processing has started.' });
      }
      setUrl('');
      setPreview(null);
      router.push('/queue');
    } catch (err) {
      toast({ variant: 'destructive', title: 'Could not start', description: apiErrorMessage(err) });
    }
  }

  const starting = processVideo.isPending || processPlaylist.isPending;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Submit Videos</h1>
        <p className="text-sm text-muted-foreground">
          Paste a single YouTube video URL or an entire playlist URL.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">YouTube URL</CardTitle>
          <CardDescription>
            We auto-detect whether the link is a single video or a playlist.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            placeholder="https://www.youtube.com/watch?v=… or /playlist?list=…"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onValidate()}
          />
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={onValidate} loading={validate.isPending} disabled={!url.trim()}>
              Validate URL
            </Button>
            <Button onClick={onStart} loading={starting} disabled={!url.trim()}>
              <PlayCircle className="h-4 w-4" />
              Start Processing
            </Button>
          </div>
        </CardContent>
      </Card>

      {preview && (
        <Card>
          <CardContent className="flex items-start gap-4 p-5">
            {preview.valid ? (
              preview.thumbnail ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={preview.thumbnail} alt="" className="h-20 w-32 shrink-0 rounded object-cover" />
              ) : (
                <div className="flex h-20 w-32 shrink-0 items-center justify-center rounded bg-muted">
                  <ListVideo className="h-7 w-7 text-muted-foreground" />
                </div>
              )
            ) : (
              <div className="flex h-20 w-32 shrink-0 items-center justify-center rounded bg-destructive/10">
                <AlertCircle className="h-7 w-7 text-destructive" />
              </div>
            )}
            <div className="min-w-0 flex-1 space-y-1">
              {preview.valid ? (
                <>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-success" />
                    <Badge variant={preview.type === 'playlist' ? 'warning' : 'secondary'}>
                      {preview.type === 'playlist' ? 'Playlist' : 'Single Video'}
                    </Badge>
                  </div>
                  <p className="truncate font-medium">{preview.title}</p>
                  {preview.channel_name && (
                    <p className="text-sm text-muted-foreground">{preview.channel_name}</p>
                  )}
                  {preview.type === 'playlist' && (
                    <p className="text-sm text-muted-foreground">
                      {preview.item_count} videos found
                    </p>
                  )}
                </>
              ) : (
                <>
                  <p className="font-medium text-destructive">Invalid URL</p>
                  <p className="text-sm text-muted-foreground">{preview.message}</p>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
