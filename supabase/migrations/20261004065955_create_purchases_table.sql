-- Compras registradas por el usuario desde el bot de Telegram
create table if not exists public.purchases (
    id            bigint generated always as identity primary key,
    user_id       text not null,                          -- mismo formato que el thread_id: "telegram-<user_id>"
    description   text not null,                          -- qué compró: "Leche y pan"
    amount        numeric(12, 2) not null check (amount >= 0),
    currency      char(3) not null default 'USD',         -- código ISO 4217
    quantity      integer not null default 1 check (quantity > 0),
    category      text,                                   -- comida, transporte, hogar, etc.
    store         text,                                   -- dónde compró
    purchased_at  date not null default current_date,     -- día de la compra
    created_at    timestamptz not null default now()      -- cuándo se registró
);

comment on table public.purchases is 'Compras registradas por el usuario a través del agente';

-- Consultas típicas: compras de un usuario por fecha y por categoría
create index if not exists purchases_user_date_idx on public.purchases (user_id, purchased_at desc);
create index if not exists purchases_user_category_idx on public.purchases (user_id, category);

-- RLS sin políticas: bloquea el acceso desde la API pública de Supabase (anon/authenticated).
-- La app se conecta con el usuario postgres, que no está sujeto a RLS.
alter table public.purchases enable row level security;
