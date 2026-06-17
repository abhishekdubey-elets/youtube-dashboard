'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Video as VideoIcon,
  CheckCircle2,
  Loader,
  XCircle,
  FileText,
  Timer,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from '@/components/status-badge';
import { useStats } from '@/lib/queries';
import { formatNumber, formatSeconds, formatDate } from '@/lib/utils';

const STAT_CARDS = [
  { key: 'total_videos', label: 'Total Videos', icon: VideoIcon, color: 'text-primary' },
  { key: 'completed', label: 'Completed', icon: CheckCircle2, color: 'text-success' },
  { key: 'in_progress', label: 'In Progress', icon: Loader, color: 'text-warning' },
  { key: 'failed', label: 'Failed', icon: XCircle, color: 'text-destructive' },
] as const;

export default function DashboardPage() {
  const { data, isLoading, isError } = useStats();

  const successData = React.useMemo(() => {
    const rate = data?.success_rate ?? 0;
    return [
      { name: 'Success', value: rate },
      { name: 'Rest', value: Math.max(0, 100 - rate) },
    ];
  }, [data?.success_rate]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Overview of the elets YouTube transcript pipeline.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {STAT_CARDS.map((c) => {
          const Icon = c.icon;
          return (
            <Card key={c.key}>
              <CardContent className="flex items-center gap-4 p-5">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-muted">
                  <Icon className={`h-5 w-5 ${c.color}`} />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">{c.label}</p>
                  {isLoading ? (
                    <Skeleton className="mt-1 h-6 w-12" />
                  ) : (
                    <p className="text-2xl font-bold">{formatNumber(data?.[c.key])}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}

        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-muted">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Avg Transcript</p>
              {isLoading ? (
                <Skeleton className="mt-1 h-6 w-16" />
              ) : (
                <p className="text-2xl font-bold">
                  {formatNumber(data?.avg_transcript_length)}
                  <span className="ml-1 text-xs font-normal text-muted-foreground">words</span>
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 p-5">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-muted">
              <Timer className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Avg Processing</p>
              {isLoading ? (
                <Skeleton className="mt-1 h-6 w-16" />
              ) : (
                <p className="text-2xl font-bold">
                  {formatSeconds(data?.avg_processing_time)}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Daily Processing (14 days)</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {isError ? (
              <ChartError />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data?.daily ?? []}>
                  <defs>
                    <linearGradient id="dailyFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      background: 'hsl(var(--popover))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    fill="url(#dailyFill)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Success Rate</CardTitle>
          </CardHeader>
          <CardContent className="relative h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={successData}
                  dataKey="value"
                  innerRadius={70}
                  outerRadius={95}
                  startAngle={90}
                  endAngle={-270}
                  paddingAngle={2}
                >
                  <Cell fill="hsl(var(--success))" />
                  <Cell fill="hsl(var(--muted))" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-bold">{(data?.success_rate ?? 0).toFixed(0)}%</span>
              <span className="text-xs text-muted-foreground">completed</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Monthly Processing</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          {isError ? (
            <ChartError />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.monthly ?? []}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  cursor={{ fill: 'hsl(var(--muted))', opacity: 0.4 }}
                  contentStyle={{
                    background: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Recent videos */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Videos</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (data?.recent_videos?.length ?? 0) === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No videos yet.</p>
          ) : (
            <div className="divide-y divide-border">
              {data?.recent_videos.map((v) => (
                <Link
                  key={v.id}
                  href={v.status === 'completed' ? `/summary/${v.id}` : '/queue'}
                  className="flex items-center gap-3 py-3 transition-colors hover:bg-muted/40"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={v.thumbnail ?? `https://i.ytimg.com/vi/${v.youtube_video_id}/hqdefault.jpg`}
                    alt=""
                    className="h-10 w-16 shrink-0 rounded object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{v.video_title}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {v.channel_name ?? '—'} · {formatDate(v.created_at)}
                    </p>
                  </div>
                  <StatusBadge status={v.status} />
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ChartError() {
  return (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      Unable to load chart data.
    </div>
  );
}
