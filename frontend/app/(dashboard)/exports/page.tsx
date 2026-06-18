'use client';

import * as React from 'react';
import { Sheet, Send, FileSpreadsheet, CheckCircle2, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useExports, useExportToSheet } from '@/lib/queries';
import { useToast } from '@/hooks/use-toast';
import { apiErrorMessage, downloadExcel } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';

const PAGE_SIZE = 10;

export default function ExportsPage() {
  const { toast } = useToast();
  const exportNow = useExportToSheet();
  const [page, setPage] = React.useState(1);
  const [excelLoading, setExcelLoading] = React.useState(false);
  const { data: history, isLoading } = useExports(page, PAGE_SIZE);

  async function onExportExcel() {
    setExcelLoading(true);
    try {
      await downloadExcel();
      toast({ variant: 'success', title: 'Excel downloaded', description: 'elets_transcripts.xlsx' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Excel export failed', description: apiErrorMessage(err) });
    } finally {
      setExcelLoading(false);
    }
  }

  async function onExportNow() {
    try {
      const res = await exportNow.mutateAsync(undefined);
      toast({
        variant: res.failed > 0 ? 'warning' : 'success',
        title: 'Export complete',
        description: `${res.exported} exported, ${res.failed} failed.`,
      });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Export failed', description: apiErrorMessage(err) });
    }
  }

  const total = history?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Google Sheets Export</h1>
        <p className="text-sm text-muted-foreground">
          Push processed videos to the configured Google Sheet.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sheet className="h-4 w-4 text-success" /> Export
          </CardTitle>
          <CardDescription>
            Export every completed video (URL, title, transcript, summary, keywords,
            sentiment and more) to a Google Sheet or download as an Excel file.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row">
          <Button
            variant="outline"
            onClick={onExportExcel}
            loading={excelLoading}
            className="w-full sm:w-auto"
          >
            <FileSpreadsheet className="h-4 w-4" /> Download Excel (.xlsx)
          </Button>
          <Button onClick={onExportNow} loading={exportNow.isPending} className="w-full sm:w-auto">
            <Send className="h-4 w-4" /> Export to Google Sheet
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Export History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>When</TableHead>
                <TableHead>Video ID</TableHead>
                <TableHead>Worksheet</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={5}>
                      <Skeleton className="h-6 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              ) : (history?.items.length ?? 0) === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-sm text-muted-foreground">
                    No exports yet.
                  </TableCell>
                </TableRow>
              ) : (
                history?.items.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="text-sm">{formatDateTime(row.exported_at)}</TableCell>
                    <TableCell className="text-sm">#{row.video_id}</TableCell>
                    <TableCell className="text-sm">{row.sheet_name ?? '—'}</TableCell>
                    <TableCell>
                      {row.status === 'success' ? (
                        <span className="inline-flex items-center gap-1 text-sm text-success">
                          <CheckCircle2 className="h-4 w-4" /> Success
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-sm text-destructive">
                          <XCircle className="h-4 w-4" /> Failed
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="max-w-xs truncate text-xs text-muted-foreground">
                      {row.error_message ?? '—'}
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
          {total} exports · page {page} of {totalPages}
        </p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Prev
          </Button>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
