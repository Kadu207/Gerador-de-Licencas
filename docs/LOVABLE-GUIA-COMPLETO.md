# Guia Lovable — Gerador de Licenças Inova TI (100% das páginas)

Documento para recriar **todas** as telas no [Lovable](https://lovable.dev) caso o time prefira UI gerada lá, integrando depois com o backend FastAPI existente.

---

## 1. Contexto do produto

| Item | Valor |
|------|-------|
| Nome | **Gerador de Licenças — Inova TI** |
| URL produção | `https://licencas.inovatitech.com.br` |
| Marca | Logo oficial: `static/inova-ti-logo.jpg` (extraída de inovatitech.com.br) |
| Favicon | `static/favicon-32.png` (32×32 da logo) |
| Foto hero (OBRIGATÓRIA) | `static/public/hero-bg.jpg` — profissionais em terraço, horizonte urbano |
| Stack backend | FastAPI + Jinja2 + Postgres (não recriar API no Lovable) |
| Paleta | Fundo `#0a0e17`, superfície `#141c2b`, accent `#3b82f6`, texto `#f1f5f9` |

---

## 2. Prompt inicial para o Lovable

```
Crie um site corporativo dark mode para "Gerador de Licenças — Inova TI".

Requisitos globais:
- 100% responsivo (mobile-first, breakpoints 380px, 768px, 900px, 1200px)
- Header fixo 72px: logo 40px + texto "Gerador de Licenças" / subtítulo "Inova TI"
- Menu desktop: Suporte (link) + Entrar (botão azul)
- Menu mobile: hamburger que abre drawer vertical
- Favicon: logo Inova TI quadrada arredondada
- Fonte: Segoe UI / system-ui
- Container max-width 1120px centralizado
- Manter foto hero fornecida como background cover (não remover)

Páginas: Landing, Suporte, Login, Dashboard, Clientes, Detalhe Cliente, Admin Usuários.
```

---

## 3. Inventário de páginas (7 telas)

### 3.1 Landing `/`

**Layout:**
1. Header fixo (componente global)
2. Hero `min-height: 100svh`, background `hero-bg.jpg` + overlay gradiente escuro
3. Título centralizado + lead + 2 CTAs (Acessar painel | Central de suporte)
4. Grid 3 cards features (1 col mobile, 3 col desktop)
5. Footer © Inova TI

**Rotas backend:** `GET /` — template `public/index.html`

**Assets:** `hero-bg.jpg`, `site.css`, `site.js`

---

### 3.2 Suporte `/suporte`

**Layout:**
1. Header fixo
2. Intro centralizada (título + subtítulo)
3. Grid 2 colunas desktop / 1 col mobile:
   - Esquerda: 4 cards (Renovar, Ativar, Vencimento, Chave por produto)
   - Direita: FAQ accordion (4 perguntas) + link voltar
4. Banner contato com link inovatitech.com.br
5. Footer

**Rotas:** `GET /suporte`

---

### 3.3 Login `/app/login`

**Layout:**
- Card centralizado max 420px
- Logo 64px + "Gerador de Licenças" + "Inova TI · Acesso administrativo"
- Form: usuário, senha, botão Entrar
- Link voltar ao site

**Rotas:** `GET/POST /app/login`, `POST /login`

---

### 3.4 Dashboard `/dashboard` (autenticado)

**Layout admin (topbar azul #0078d4):**
- Logo + "Gerador de Licenças · Inova TI"
- Nav: Dashboard | Clientes | Administração | Sair

**Conteúdo:**
- KPIs (clientes, licenças ativas, bloqueadas, receita…)
- Gráficos Chart.js (donut status, barras receita)
- Tabela inadimplência
- Seção Conexões (banco local, sync legado)
- Botão sync all

**Rotas:** `GET /dashboard`, `POST /admin/sync-all`

---

### 3.5 Clientes `/clients` (autenticado)

**Formulário novo cliente:**
- Grid 2 col: nome, razão social, tipo doc, CPF/CNPJ (máscara + RF auto), emails, telefones, IDs vínculo, endereço CEP auto

**Tabela clientes:**
| Cliente | Produto(s) | Status licença | Pagamento em dia | Ação |
|---------|------------|----------------|------------------|------|

**Rotas:** `GET/POST /clients`, APIs `/api/cep/{cep}`, `/api/cnpj/{cnpj}`

---

### 3.6 Detalhe cliente `/clients/{id}` (autenticado)

- Dados do cliente
- Form emitir licença: produto (Produto 01/02/03), período, plano pagamento → **Gerar licença 25 chars**
- Tabela licenças: chave, produto, validade, status, renovar/revogar/Stripe

**Rotas:** `POST /clients/{id}/licenses`, renew, revoke, payment-link

---

### 3.7 Admin usuários `/admin/users` (autenticado)

- Form novo usuário (username, senha, nome)
- Tabela operadores: alterar senha inline, ativar/desativar

**Rotas:** `GET/POST /admin/users`, password, toggle

---

## 4. Componentes reutilizáveis (design system)

| Componente | Variantes |
|------------|-----------|
| `SiteHeader` | logo, nav links, mobile menu |
| `SiteFooter` | copyright, URL |
| `Button` | primary (azul), secondary (outline) |
| `Card` | feature, support, admin |
| `DataTable` | clientes, licenças, operadores |
| `FormField` | text, email, select, textarea + máscaras |
| `FAQAccordion` | details/summary |

---

## 5. Responsividade (obrigatório)

```css
/* Mobile ≤768px */
- Header: hamburger + nav overlay
- Hero: botões full-width max 320px
- Features: 1 coluna
- Suporte: 1 coluna (cards acima, FAQ abaixo)
- Tabelas admin: scroll horizontal ou cards empilhados

/* Tablet 769–900px */
- Features: 1–2 colunas
- Suporte: 1 coluna

/* Desktop ≥901px */
- Features: 3 colunas
- Suporte: 2 colunas lado a lado
```

---

## 6. Integração Lovable → FastAPI

O Lovable gera React/HTML estático. Para produção:

**Opção A (recomendada):** Exportar HTML/CSS do Lovable → colar em `templates/` Jinja2, manter rotas FastAPI.

**Opção B:** Lovable como frontend separado (subdomínio) chamando API REST — exige CORS e JWT.

**Opção C:** Manter templates Jinja atuais (`site.css` v3) — já espelham este guia.

### Endpoints que o front deve chamar

| Ação | Método | URL |
|------|--------|-----|
| Health | GET | `/health` |
| Login | POST | `/login` (form) |
| API licenças | POST | `/api/v1/licenses/validate` etc. |
| CEP | GET | `/api/cep/{cep}` |
| CNPJ RF | GET | `/api/cnpj/{cnpj}` |

---

## 7. Checklist visual antes de publicar

- [ ] Favicon logo Inova TI visível na aba
- [ ] Título aba: "Gerador de Licenças — Inova TI"
- [ ] Hero com foto `hero-bg.jpg` visível (overlay ≤75% opacidade)
- [ ] Header alinhado: logo esquerda, menu direita
- [ ] Mobile: menu hamburger funcional
- [ ] Suporte: cards e FAQ alinhados, sem espaço vazio excessivo
- [ ] Testar 375px, 768px, 1024px, 1440px

---

## 8. Arquivos atuais no repositório (referência)

```
static/public/hero-bg.jpg      ← MANTER
static/public/site.css         ← CSS responsivo v3
static/public/site.js          ← menu mobile
static/inova-ti-logo.jpg       ← logo marca
static/favicon-32.png          ← ícone aba
templates/public/_head.html
templates/public/_header.html
templates/public/_footer.html
templates/public/index.html
templates/public/suporte.html
templates/login.html
templates/dashboard.html
templates/clients.html
templates/client_detail.html
templates/admin_users.html
```

---

## 9. Deploy após alterações

```bash
cd /opt/gerador-licencas
git pull origin main
docker compose up -d --build license-server
```

Limpar cache browser: **Ctrl+Shift+R** ou Cloudflare → Purge Cache.

---

*Gerado para Inova TI — Gerador de Licenças. Backend: github.com/Kadu207/Gerador-de-Licencas*
