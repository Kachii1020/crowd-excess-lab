begin;

create table if not exists public.agent_audit_events (
  id bigint generated always as identity primary key,
  run_id text not null check (run_id ~ '^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$'),
  event_type text not null check (
    event_type in (
      'run_started', 'signal', 'risk_decision', 'execution', 'exit_intent',
      'position_exit', 'portfolio', 'run_completed'
    )
  ),
  recorded_at timestamptz not null default now(),
  payload jsonb not null,
  inserted_at timestamptz not null default now()
);

create index if not exists agent_audit_events_run_time_idx
  on public.agent_audit_events (run_id, recorded_at, id);
create index if not exists agent_audit_events_recent_idx
  on public.agent_audit_events (recorded_at desc);

alter table public.agent_audit_events enable row level security;

revoke all on table public.agent_audit_events from anon, authenticated;
grant select on table public.agent_audit_events to anon, authenticated;
grant select, insert on table public.agent_audit_events to service_role;
grant usage, select on sequence public.agent_audit_events_id_seq to service_role;

drop policy if exists "public can read sanitized agent audit" on public.agent_audit_events;
create policy "public can read sanitized agent audit"
  on public.agent_audit_events
  for select
  to anon, authenticated
  using (true);

create or replace function public.block_agent_audit_mutation()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
  raise exception 'agent audit events are append-only';
end;
$$;

drop trigger if exists block_agent_audit_update_delete on public.agent_audit_events;
create trigger block_agent_audit_update_delete
before update or delete on public.agent_audit_events
for each row execute function public.block_agent_audit_mutation();

commit;
