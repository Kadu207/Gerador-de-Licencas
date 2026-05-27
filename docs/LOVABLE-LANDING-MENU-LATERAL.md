# Lovable — Landing Page + Menu Lateral | Gerador de Licenças Inova TI

Documento de especificação para reconstruir no **[Lovable](https://lovable.dev)** a landing pública e o shell administrativo com **menu lateral**, preservando todas as funções e botões do sistema atual.

**Backend existente (não recriar no Lovable):** FastAPI em `https://licencas.inovatitech.com.br`  
**Repositório:** `github.com/Kadu207/Gerador-de-Licencas`

---

## 1. Prompt principal (copiar e colar no Lovable)

```
Projeto: Gerador de Licenças — Inova TI (SaaS B2B, dark mode corporativo)

Crie duas áreas:

A) LANDING PÚBLICA (visitante não logado)
B) APP ADMIN com MENU LATERAL FIXO (usuário logado)

Marca:
- Nome: Gerador de Licenças — Inova TI
- Logo: imagem quadrada arredondada (fornecida: inova-ti-logo.jpg)
- Favicon: favicon-32.png (mesma logo, 32×32)
- Site institucional: inovatitech.com.br

Paleta:
- Fundo: #0a0e17
- Superfície/cards: #141c2b
- Accent/botões primários: #3b82f6
- Texto: #f1f5f9 | Muted: #94a3b8

100% responsivo: mobile-first, breakpoints 380px, 768px, 1024px, 1280px.

HERO — VERSÃO 1 (FOTO VIVA, OBRIGATÓRIA):
- Usar imagem fornecida hero-bg.jpg (profissionais em terraço, pôr do sol laranja/azul)
- Layout SPLIT (não sobrepor texto em cima da foto com overlay pesado):
  • Bloco superior: 58vh min, foto em cover, overlay LEVE apenas no rodapé da foto (gradiente transparente → #0a0e17, opacidade máx 35%)
  • Bloco inferior: fundo sólido #0a0e17, título + subtítulo + 2 botões centralizados
- A foto deve aparecer VIVA (cores quentes do pôr do sol visíveis), como referência visual anexa

Header público fixo (72px): logo + "Gerador de Licenças / Inova TI" | links Suporte + botão Entrar
Mobile: hamburger → drawer

Menu lateral admin (260px desktop, drawer mobile):
- Logo + nome no topo
- Itens de navegação com ícones
- Rodapé do menu: usuário logado + Sair
- Conteúdo principal à direita com scroll

Não inventar novas funcionalidades — apenas UI das rotas listadas neste documento.
```

---

## 2. Assets obrigatórios (anexar no Lovable)

| Arquivo | Uso | Caminho no repo |
|---------|-----|-----------------|
| **hero-bg.jpg** | Hero v1 — foto viva no topo | `static/public/hero-bg.jpg` |
| **inova-ti-logo.jpg** | Logo header, menu lateral, login | `static/inova-ti-logo.jpg` |
| **favicon-32.png** | Ícone da aba do navegador | `static/favicon-32.png` |

> A **versão 1 da foto** é caracterizada pelo **pôr do sol visível e saturado** na metade superior da tela, com o texto e botões **abaixo** da imagem (não em overlay escuro sobre ela).

---

## 3. Landing Page — layout v1 (foto viva)

### 3.1 Estrutura visual (wireframe)

```
┌─────────────────────────────────────────────────────────┐
│  [LOGO] Gerador de Licenças · Inova TI    Suporte [Entrar] │  ← header fixo 72px
├─────────────────────────────────────────────────────────┤
│                                                         │
│     FOTO hero-bg.jpg — CORES VIVAS (pôr do sol)         │  ← 58vh, overlay leve
│     profissionais olhando horizonte urbano              │     só fade inferior
│                                                         │
├─────────────────────────────────────────────────────────┤
│              fundo sólido #0a0e17                        │
│                                                         │
│     Gerenciamento centralizado de licenças              │
│     Emissão, vínculo e controle de licenças digitais…   │
│                                                         │
│     [ Acessar painel ]  [ Central de suporte ]          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │ Chaves 25   │ │ Alertas     │ │ Pagamentos  │        │  ← 3 cards
│  │ caracteres  │ │ automáticos │ │ integrados  │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
├─────────────────────────────────────────────────────────┤
│        © 2026 Inova TI · licencas.inovatitech.com.br   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 CSS de referência — overlay leve (foto viva)

```css
.hero-photo {
  height: 58vh;
  min-height: 320px;
  background: url("/static/public/hero-bg.jpg") center 35% / cover no-repeat;
  position: relative;
}

/* Fade suave apenas na transição para o bloco de texto — NÃO escurecer a foto inteira */
.hero-photo::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 40%;
  background: linear-gradient(to bottom, transparent, #0a0e17);
}

.hero-content {
  background: #0a0e17;
  padding: 3rem 1.5rem 4rem;
  text-align: center;
  max-width: 720px;
  margin: 0 auto;
}
```

**Evitar** (versões que apagam a foto):
- `min-height: 100vh` com overlay `rgba(10,14,23,0.85)` sobre texto e imagem juntos
- `<img>` no fluxo do documento empurrando conteúdo (quebra layout)

### 3.3 Conteúdo textual (copy exato)

**Título:** Gerenciamento centralizado de licenças

**Subtítulo:** Emissão, vínculo e controle de licenças digitais para todos os produtos da Inova TI — cada cliente com chaves independentes de 25 caracteres.

**Botões:**

| Label | Ação | Rota |
|-------|------|------|
| Acessar painel | primário azul | `/app/login` |
| Central de suporte | secundário outline | `/suporte` |

**Cards (3):**

1. **Chaves de 25 caracteres** — Emissão segura com validação remota via API HTTPS.
2. **Alertas automáticos** — Notificações por e-mail antes do vencimento da licença.
3. **Pagamentos integrados** — Cartão, PIX e boleto com confirmação automática de renovação.

**Título da aba:** `Gerador de Licenças — Inova TI`

### 3.4 Header público (visitante)

| Elemento | Comportamento |
|----------|---------------|
| Logo 40×40 | Link para `/` |
| Texto marca | "Gerador de Licenças" + subtítulo "Inova TI" |
| Suporte | Link `/suporte` |
| Entrar | Botão azul → `/app/login` |
| Logado | Substituir "Entrar" por "Painel" → `/dashboard` |

---

## 4. Menu lateral — funções e botões existentes

O app admin hoje usa topbar; no Lovable deve ser **sidebar fixa** com os mesmos destinos.

### 4.1 Itens do menu lateral (sempre visíveis quando logado)

| # | Ícone sugerido | Label | Rota | Descrição |
|---|----------------|-------|------|-----------|
| 1 | LayoutDashboard | Dashboard | `GET /dashboard` | KPIs, gráficos, inadimplência |
| 2 | Users | Clientes | `GET /clients` | Cadastro e listagem |
| 3 | Settings | Administração | `GET /admin/users` | Usuários e senhas |
| — | — | — | — | — |
| 4 | LogOut | Sair | `GET /logout` | Encerra sessão |

**Rodapé do sidebar:** avatar/inicial + `{{ user.nome or user.username }}`

### 4.2 Botões por tela (replicar no Lovable)

#### Dashboard `/dashboard`

| Botão | Método | Ação |
|-------|--------|------|
| Sincronizar licenças | POST | `/admin/sync-all` |

**KPIs exibidos:** Clientes, Licenças totais, Ativas, Em carência, Bloqueadas, Vencidas, Receita efetivada, Pagamentos confirmados, Pagamentos pendentes, Inadimplentes.

**Gráficos (Chart.js):** Licenças por software, Status operacional, Receita mensal, Inadimplência por software, Receita por plano.

**Tabelas:** Inadimplência detalhada, Pagamentos recentes, Conexões (banco local / sync legado).

**Link por linha:** "Abrir" / "Gerenciar" → `/clients/{id}`

---

#### Clientes `/clients`

| Botão | Método | Ação |
|-------|--------|------|
| Cadastrar cliente | POST | `/clients` |

**Formulário — campos:**

- Nome fantasia *, Razão social, Tipo documento (CNPJ/CPF)
- CPF/CNPJ (máscara + consulta RF automática ao completar 14 dígitos)
- E-mail 01/02, Telefone 01/02/03
- Matriz (filial de), ID vínculo produto 01, ID vínculo produto 02
- Endereço: CEP (auto ViaCEP), UF, Logradouro, Número, Complemento, Bairro, Cidade, Observações

**Tabela clientes:**

| Coluna | Conteúdo |
|--------|----------|
| Cliente | Nome + documento |
| Produto(s) | Resumo licenças |
| Status da licença | Em vigor / Expirada / Sem licença |
| Pagamento em dia | Sim / Não |
| Ação | **Gerenciar** → `/clients/{id}` |

---

#### Detalhe cliente `/clients/{id}`

| Botão | Método | Ação |
|-------|--------|------|
| Gerar licença (25 caracteres) | POST | `/clients/{id}/licenses` |
| Renovar | POST | `/licenses/{id}/renew` |
| Revogar | POST | `/licenses/{id}/revoke` |
| Link Stripe | POST | `/licenses/{id}/payment-link` |
| Cancelar cliente por inadimplência | POST | `/clients/{id}/cancel` |

**Form emitir licença:** Software (Produto 01/02/03), Período, Plano pagamento, Observações.

**Tabela licenças:** Chave (25 chars), Produto, Período, Validade, Restante, Status, Ações.

**Link:** ← Voltar para clientes → `/clients`

---

#### Administração `/admin/users`

| Botão | Método | Ação |
|-------|--------|------|
| Cadastrar usuário | POST | `/admin/users` |
| Salvar (senha) | POST | `/admin/users/{id}/password` |
| Ativar / Desativar | POST | `/admin/users/{id}/toggle` |

**Tabela:** Usuário, Nome, Status (Ativo/Inativo), Alterar senha inline.

---

#### Login `/app/login`

| Botão | Método | Ação |
|-------|--------|------|
| Entrar | POST | `/login` ou `/app/login` |

Campos: Usuário, Senha. Link: ← Voltar ao site → `/`

---

### 4.3 Wireframe menu lateral + conteúdo

```
Desktop (≥1024px):
┌──────────────┬────────────────────────────────────────┐
│ [LOGO]       │  Dashboard                             │
│ Gerador      │  ─────────────────────────────────     │
│ Inova TI     │  [conteúdo da página]                  │
│              │                                        │
│ ■ Dashboard  │                                        │
│ ■ Clientes   │                                        │
│ ■ Admin      │                                        │
│              │                                        │
│ ──────────── │                                        │
│ 👤 admin     │                                        │
│   Sair       │                                        │
└──────────────┴────────────────────────────────────────┘
     260px                    flex 1

Mobile (≤768px):
- Sidebar oculta; botão ☰ abre drawer sobre conteúdo
- Mesmos itens do menu
```

### 4.4 CSS sidebar de referência

```css
.app-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: #0d121c;
  border-right: 1px solid rgba(255,255,255,0.08);
  display: flex;
  flex-direction: column;
  padding: 1.25rem 0;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  color: #94a3b8;
  text-decoration: none;
}

.sidebar-nav a.active,
.sidebar-nav a:hover {
  background: rgba(59, 130, 246, 0.12);
  color: #f1f5f9;
}

.main-content {
  flex: 1;
  overflow: auto;
  padding: 1.5rem 2rem;
  background: #f3f2f1; /* admin claro — igual styles.css atual */
}
```

---

## 5. Páginas públicas adicionais

### Suporte `/suporte`

Mesmo header público da landing. Layout:

1. Intro centralizada
2. Grid 2 col (desktop): cards à esquerda + FAQ accordion à direita
3. Banner contato → inovatitech.com.br
4. Link ← Voltar ao início

**Título aba:** `Suporte — Gerador de Licenças Inova TI`

---

## 6. Responsividade — checklist Lovable

| Viewport | Landing | Sidebar |
|----------|---------|---------|
| 375px (mobile) | Foto 50vh, botões full-width, menu hamburger | Drawer sidebar |
| 768px (tablet) | Foto 55vh, cards 1 coluna | Drawer ou sidebar estreita |
| 1024px+ | Foto 58vh, cards 3 colunas | Sidebar 260px fixa |
| 1440px | Container max 1120px centralizado | Idem |

---

## 7. Integração Lovable → FastAPI (após design)

1. **Exportar** HTML/CSS/JS do Lovable.
2. **Landing + Suporte:** colar em `templates/public/` (Jinja2), manter rotas `GET /` e `GET /suporte`.
3. **Admin com sidebar:** substituir `topbar` em `dashboard.html`, `clients.html`, `client_detail.html`, `admin_users.html` por partial `templates/_sidebar.html`.
4. **Form actions:** manter `method="post"` e `action` das rotas FastAPI — não alterar backend.
5. **Assets:** copiar para `static/` e servir via `/static/...`.

### APIs auxiliares (forms clientes)

```
GET /api/cep/{cep}      → preenche endereço
GET /api/cnpj/{cnpj}    → preenche razão social / nome (Receita Federal)
```

### API licenças (produtos externos — referência)

```
POST /api/v1/licenses/validate
POST /api/v1/licenses/activate
GET  /api/v1/licenses/status
GET  /api/v1/licenses/heartbeat
```

---

## 8. Comparativo hero — versões

| Versão | Comportamento | Usar no Lovable? |
|--------|---------------|------------------|
| **v1 — Foto viva** | Foto no topo (~58vh), overlay leve, texto **abaixo** em fundo sólido | **SIM (pedido do cliente)** |
| v2 | Texto sobre foto com overlay 75–92% | Não |
| v3 | `100vh` + overlay médio, texto centrado na foto | Não |

---

## 9. Entregáveis esperados do Lovable

- [ ] Landing com hero v1 (foto viva split)
- [ ] Header público responsivo
- [ ] Página Suporte alinhada ao design system
- [ ] Shell admin com menu lateral + 4 telas (Dashboard, Clientes, Detalhe, Admin)
- [ ] Login centralizado com logo Inova TI
- [ ] Favicon logo na aba
- [ ] Todos os botões/ações da seção 4.2 presentes
- [ ] Mobile testado 375px e 768px

---

## 10. Deploy após integrar templates

```bash
cd /opt/gerador-licencas
git pull origin main
docker compose up -d --build license-server
```

Cloudflare: Purge Cache + hard refresh (`Ctrl+Shift+R`).

---

*Documento gerado para Inova TI — Gerador de Licenças. Hero: manter `hero-bg.jpg` versão 1 (cores vivas). Menu lateral: espelha funções atuais do FastAPI.*
