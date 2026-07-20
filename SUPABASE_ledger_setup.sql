-- THE FAR LEDGER (meta-achievements leaderboard) — v1, 2026-07-17
-- Run this in the Supabase SQL editor (same project as city_traffic).
-- Table: one row per told-name; counts only ever rise; majors merge across devices.

create table if not exists sr_ledger(
  name         text primary key,
  majors       jsonb       not null default '{}'::jsonb,
  major_count  int         not null default 0,
  slaves_freed int         not null default 0,
  cities       int         not null default 0,
  goods        int         not null default 0,
  updated_at   timestamptz not null default now()
);

alter table sr_ledger enable row level security;

drop policy if exists sr_ledger_read on sr_ledger;
create policy sr_ledger_read on sr_ledger for select using (true);
-- no insert/update policy: writes go only through the RPC below

create or replace function submit_ledger(
  p_name text, p_majors jsonb, p_major_count int,
  p_slaves int, p_cities int, p_goods int)
returns void
language plpgsql security definer set search_path = public as $$
begin
  if p_name is null or length(trim(p_name)) = 0 or length(p_name) > 40 then return; end if;
  insert into sr_ledger(name, majors, major_count, slaves_freed, cities, goods, updated_at)
  values (trim(p_name), coalesce(p_majors,'{}'::jsonb), coalesce(p_major_count,0),
          coalesce(p_slaves,0), coalesce(p_cities,0), coalesce(p_goods,0), now())
  on conflict (name) do update set
    majors       = sr_ledger.majors || coalesce(excluded.majors,'{}'::jsonb),
    major_count  = (select count(*) from jsonb_object_keys(sr_ledger.majors || coalesce(excluded.majors,'{}'::jsonb))),
    slaves_freed = greatest(sr_ledger.slaves_freed, excluded.slaves_freed),
    cities       = greatest(sr_ledger.cities, excluded.cities),
    goods        = greatest(sr_ledger.goods, excluded.goods),
    updated_at   = now();
end $$;

grant execute on function submit_ledger(text, jsonb, int, int, int, int) to anon;
