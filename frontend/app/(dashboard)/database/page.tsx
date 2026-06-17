'use client';

import * as React from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  ChevronLeft,
  ChevronRight,
  Pencil,
  RotateCw,
  Trash2,
  ExternalLink,
  Search,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/status-badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  useDeleteVideo,
  useReprocessVideo,
  useUpdateSummary,
  useVideos,
} from '@/lib/queries';
import { getSummary } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { apiErrorMessage } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import type { Video, VideoStatus } from '@/lib/types';

const STATUSES: VideoStatus[] = [
  'queued',
  'downloading',
  'extracting',
  'transcribing',
  'summarizing',
  'exporting',
  'completed',
  'failed',
  'cancelled',
];

const PAGE_SIZE = 10;

export const dynamic = 'force-dynamic';

export default function DatabasePage() {
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const [search, setSearch] = React.useState(searchParams.get('search') ?? '');
  const [debounced, setDebounced] = React.useState(search);
  const [status, setStatus] = React.useState('');
  const [sort, setSort] = React.useState('-created_at');
  const [page, setPage] = React.useState(1);

  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  React.useEffect(() => setPage(1), [debounced, status, sort]);

  const { data, isLoading } = useVideos({
    page,
    page_size: PAGE_SIZE,
    search: debounced || undefined,
    status: status || undefined,
    sort,
  });

  const reprocess = useReprocessVideo();
  const del = useDeleteVideo();

  const [editing, setEditing] = React.useState<Video | null>(null);
  const [deleting, setDeleting] = React.useState<Video | null>(null);
  const [summaryText, setSummaryText] = React.useState('');
  const [loadingSummary, setLoadingSummary] = React.useState(false);
  const updateSummary = useUpdateSummary(editing?.id ?? 0);

  async function openEdit(v: Video) {
    setEditing(v);
    setSummaryText('');
    setLoadingSummary(true);
    try {
      const s = await getSummary(v.id);
      setSummaryText(s.summary ?? '');
    } catch {
      setSummaryText('');
    } finally {
      setLoadingSummary(false);
    }
  }

  async function saveSummary() {
    if (!editing) return;
    try {
      await updateSummary.mutateAsync({ summary: summaryText });
      toast({ variant: 'success', title: 'Summary updated' });
      setEditing(null);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Update failed', description: apiErrorMessage(err) });
    }
  }

  async function confirmDelete() {
    if (!deleting) return;
    try {
      await del.mutateAsync(deleting.id);
      toast({ variant: 'success', title: 'Deleted', description: deleting.video_title });
      setDeleting(null);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Delete failed', description: apiErrorMessage(err) });
    }
  }

  async function onReprocess(v: Video) {
    try {
      await reprocess.mutateAsync(v.id);
      toast({ variant: 'success', title: 'Reprocessing', description: v.video_title });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Failed', description: apiErrorMessage(err) });
    }
  }

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const items = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Database Explorer</h1>
        <p className="text-sm text-muted-foreground">Search, filter and manage every processed video.</p>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative min-w-[200px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Search title or channel…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-44">
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </Select>
          <Select value={sort} onChange={(e) => setSort(e.target.value)} className="w-48">
            <option value="-created_at">Newest first</option>
            <option value="created_at">Oldest first</option>
            <option value="video_title">Title A–Z</option>
            <option value="-video_title">Title Z–A</option>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Video</TableHead>
                <TableHead>Channel</TableHead>
                <TableHead>Playlist</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={6}>
                      <Skeleton className="h-8 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              ) : items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-12 text-center text-sm text-muted-foreground">
                    No videos found.
                  </TableCell>
                </TableRow>
              ) : (
                items.map((v) => (
                  <TableRow key={v.id}>
                    <TableCell className="max-w-xs">
                      <Link href={`/summary/${v.id}`} className="flex items-center gap-2 font-medium hover:text-primary">
                        <span className="truncate">{v.video_title}</span>
                        <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                      </Link>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{v.channel_name ?? '—'}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{v.playlist_name ?? '—'}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatDate(v.created_at)}</TableCell>
                    <TableCell>
                      <StatusBadge status={v.status} />
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Edit summary"
                          onClick={() => openEdit(v)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Reprocess"
                          onClick={() => onReprocess(v)}
                        >
                          <RotateCw className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Delete"
                          onClick={() => setDeleting(v)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {total} records · page {page} of {totalPages}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft className="h-4 w-4" /> Prev
          </Button>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Edit summary dialog */}
      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogHeader>
          <DialogTitle>Edit Summary</DialogTitle>
          <DialogDescription className="truncate">{editing?.video_title}</DialogDescription>
        </DialogHeader>
        {loadingSummary ? (
          <Skeleton className="h-40 w-full" />
        ) : (
          <Textarea
            rows={10}
            value={summaryText}
            onChange={(e) => setSummaryText(e.target.value)}
            placeholder="Executive summary…"
          />
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => setEditing(null)}>
            Cancel
          </Button>
          <Button onClick={saveSummary} loading={updateSummary.isPending}>
            Save changes
          </Button>
        </DialogFooter>
      </Dialog>

      {/* Delete confirm dialog */}
      <Dialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)}>
        <DialogHeader>
          <DialogTitle>Delete video?</DialogTitle>
          <DialogDescription>
            This permanently removes “{deleting?.video_title}” and its transcript, summary and
            export records. This cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => setDeleting(null)}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={confirmDelete} loading={del.isPending}>
            Delete
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
}
