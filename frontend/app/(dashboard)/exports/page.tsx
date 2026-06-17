'use client';

import * as React from 'react';
import { Sheet, Upload, Send, CheckCircle2, XCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useExportConfig,
  useExports,
  useExportToSheet,
  useUpdateExportConfig,
  useUploadCredentials,
} from '@/lib/queries';
import { useToast } from '@/hooks/use-toast';
import { apiErrorMessage } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';

const PAGE_SIZE = 10;

export default function ExportsPage() {
  const { toast } = useToast();
  const { data: config, isLoading: loadingConfig } = useExportConfig();
  const updateConfig = useUpdateExportConfig();
  const uploadCreds = useUploadCredentials();
  const exportNow = useExportToSheet();

  const [spreadsheetId, setSpreadsheetId] = React.useState('');
  const [worksheet, setWorksheet] = React.useState('');
  const [auto, setAuto] = React.useState(false);
  const [page, setPage] = React.useState(1);
  const fileRef = React.useRef<HTMLInputElement>(null);

  const { data: history, isLoading: loadingHistory } = useExports(page, PAGE_SIZE);

  React.useEffect(() => {
    if (config) {
      setSpreadsheetId(config.spreadsheet_id ?? '');
      setWorksheet(config.worksheet_name ?? '');
      setAuto(config.auto_export ?? false);
    }
  }, [config]);

  async function saveConfig() {
    try {
      await updateConfig.mutateAsync({
        spreadsheet_id: spreadsheetId,
        worksheet_name: worksheet,
        auto_export: auto,
      });
      toast({ variant: 'success', title: 'Configuration saved' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Save failed', description: apiErrorMessage(err) });
    }
  }

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadCreds.mutateAsync(file);
      toast({ variant: 'success', title: 'Credentials uploaded' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Upload failed', description: apiErrorMessage(err) });
    } finally {
      if (fileRef.current) fileRef.current.value = '';
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
          Configure and trigger automatic exports of processed videos.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sheet className="h-4 w-4 text-success" /> Configuration
            </CardTitle>
            <CardDescription>Target spreadsheet and worksheet.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loadingConfig ? (
              <Skeleton className="h-32 w-full" />
            ) : (
              <>
                <div className="space-y-2">
                  <Label htmlFor="sid">Spreadsheet ID</Label>
                  <Input
                    id="sid"
                    value={spreadsheetId}
                    onChange={(e) => setSpreadsheetId(e.target.value)}
                    placeholder="1AbCdEf…"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ws">Worksheet Name</Label>
                  <Input
                    id="ws"
                    value={worksheet}
                    onChange={(e) => setWorksheet(e.target.value)}
                    placeholder="Transcripts"
                  />
                </div>
                <div className="flex items-center justify-between rounded-lg border border-border p-3">
                  <div>
                    <p className="text-sm font-medium">Auto Export</p>
                    <p className="text-xs text-muted-foreground">
                      Append each video automatically when processing completes.
                    </p>
                  </div>
                  <Switch checked={auto} onCheckedChange={setAuto} />
                </div>
                <Button onClick={saveConfig} loading={updateConfig.isPending} className="w-full">
                  Save configuration
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Upload className="h-4 w-4 text-primary" /> Credentials &amp; Actions
            </CardTitle>
            <CardDescription>Service-account JSON and manual export.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-border p-3">
              <div className="flex items-center gap-2">
                {config?.credentials_uploaded ? (
                  <Badge variant="success">Credentials uploaded</Badge>
                ) : (
                  <Badge variant="warning">No credentials</Badge>
                )}
              </div>
              <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()} loading={uploadCreds.isPending}>
                <Upload className="h-4 w-4" /> Upload JSON
              </Button>
              <input
                ref={fileRef}
                type="file"
                accept="application/json,.json"
                className="hidden"
                onChange={onUpload}
              />
            </div>

            <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
              Share your spreadsheet with the service-account email (found inside the JSON,
              field <code className="rounded bg-muted px-1">client_email</code>) as an Editor.
            </div>

            <Button onClick={onExportNow} loading={exportNow.isPending} className="w-full">
              <Send className="h-4 w-4" /> Export all completed now
            </Button>
          </CardContent>
        </Card>
      </div>

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
              {loadingHistory ? (
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
