from app.schemas import AppPlan

TYPE_MAP = {
    "text": "text",
    "textarea": "text",
    "number": "numeric",
    "boolean": "boolean",
    "date": "date",
    "select": "text",
}


def generate_sql(plan: AppPlan) -> str:
    statements = [
        "-- Auto-generated Supabase PostgreSQL Schema by NovaBuild",
        "-- Enable UUID extension if not enabled",
        'create extension if not exists "uuid-ossp";',
        "",
        "-- Trigger function to auto-update updated_at timestamp",
        "create or replace function update_modified_column()",
        "returns trigger as $$",
        "begin",
        "  new.updated_at = now();",
        "  return new;",
        "end;",
        "$$ language 'plpgsql';",
        ""
    ]

    for entity in plan.entities:
        table = entity.plural.lower()
        cols = ",\n".join(
            f"  {f.name} {TYPE_MAP.get(f.type, 'text')}{' not null' if f.required else ''}"
            for f in entity.fields
        )

        statements.append(f"""-- Table: {table}
create table if not exists {table} (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade not null,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null,
{cols}
);

-- Index for user tenancy
create index if not exists idx_{table}_user_id on {table}(user_id);
create index if not exists idx_{table}_created_at on {table}(created_at desc);

-- Enable Row Level Security (RLS)
alter table {table} enable row level security;

-- Policies for owner isolation
drop policy if exists "{table}_select_policy" on {table};
create policy "{table}_select_policy" on {table}
  for select using (auth.uid() = user_id);

drop policy if exists "{table}_insert_policy" on {table};
create policy "{table}_insert_policy" on {table}
  for insert with check (auth.uid() = user_id);

drop policy if exists "{table}_update_policy" on {table};
create policy "{table}_update_policy" on {table}
  for update using (auth.uid() = user_id);

drop policy if exists "{table}_delete_policy" on {table};
create policy "{table}_delete_policy" on {table}
  for delete using (auth.uid() = user_id);

-- Trigger for updated_at
drop trigger if exists set_timestamp_{table} on {table};
create trigger set_timestamp_{table}
  before update on {table}
  for each row execute procedure update_modified_column();
""")

    return "\n".join(statements)