-- Execute uma única vez no SQL Editor do projeto Supabase.
-- O app acessa esta tabela somente pelo servidor do Streamlit.

create table if not exists public.app_state (
    namespace text not null,
    record_key text not null,
    payload jsonb not null,
    updated_at timestamptz not null default now(),
    primary key (namespace, record_key)
);

alter table public.app_state enable row level security;

-- O navegador não acessa a tabela diretamente. A chave pública fica sem permissão.
revoke all on table public.app_state from anon, authenticated;
grant all on table public.app_state to service_role;

comment on table public.app_state is
    'Estado persistente do Treinador IDECAN: usuários, progresso e simulados.';
