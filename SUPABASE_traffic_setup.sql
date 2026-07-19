-- THE CARAVAN CYCLE — run this once in the Supabase SQL editor (Kris, 7/17; v2 YEAR-AWARE)
-- Rows are (city, era, gyear): 762 and 1271 tracked separately, and every visit records the
-- IN-GAME YEAR — so the future variable-start feature (1258–1271, the elder Polos, the Mongol
-- expansion) can window by year and weight nearby years, without a schema change. Today's
-- client simply sums a city's visits across years within its era.
-- If you already ran the v1 script, run the two DROP lines first; the table was empty anyway.

drop function if exists bump_city_traffic(text, text);
drop table if exists city_traffic;

create table if not exists city_traffic (
  city text not null,
  era  text not null default '1271',
  gyear int not null default 0,          -- in-game Julian year of the visit (e.g. 1271, 1272…)
  visits bigint not null default 0,
  updated_at timestamptz default now(),
  primary key (city, era, gyear)
);

alter table city_traffic enable row level security;

drop policy if exists "traffic readable by all" on city_traffic;
create policy "traffic readable by all" on city_traffic
  for select using (true);

-- no insert/update policy for anon: all writes go through the RPC below

create or replace function bump_city_traffic(p_city text, p_era text default '1271', p_gyear int default 0)
returns void
language sql
security definer
set search_path = public
as $$
  insert into city_traffic (city, era, gyear, visits)
  values (p_city, p_era, p_gyear, 1)
  on conflict (city, era, gyear)
  do update set visits = city_traffic.visits + 1, updated_at = now();
$$;

grant execute on function bump_city_traffic(text, text, int) to anon;
