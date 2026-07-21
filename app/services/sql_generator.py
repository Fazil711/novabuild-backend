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
    statements = []

    for entity in plan.entities:
        table = entity.plural.lower()
        cols = ",\n".join(
            f"  {f.name} {TYPE_MAP[f.type]}{' not null' if f.required else ''}"
            for f in entity.fields
        )

        statements.append(f"""create table if not exists {table} (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) not null,
  created_at timestamptz default now(),
{cols}
);

alter table {table} enable row level security;

create policy "{table}_owner_access" on {table}
  for all using (auth.uid() = user_id);
""")

    return "\n".join(statements)