# jClaw

## Plataforma de Orquestração de Agentes IA

### Especificação Técnica de Referência

| Metadado | Valor |
|---|---|
| Versão do Documento | 2.0.0 |
| Data | Abril 2026 |
| Linguagem Principal | Python 3.11+ |
| Licença | Proprietária |
| Status | Draft — Em validação |

---

## Índice

1. [Visão Geral e Objetivos](#1-visão-geral-e-objetivos)
2. [Arquitetura da Plataforma](#2-arquitetura-da-plataforma)
3. [Core Engine — Orquestrador de Agentes](#3-core-engine--orquestrador-de-agentes)
4. [Sistema de Memória de Sessão](#4-sistema-de-memória-de-sessão)
5. [Handoffs entre Agentes](#5-handoffs-entre-agentes)
6. [Suporte Multi-LLM](#6-suporte-multi-llm)
7. [Sistema de Skills](#7-sistema-de-skills)
8. [Canais de Comunicação (Telegram / WhatsApp)](#8-canais-de-comunicação-telegram--whatsapp)
9. [Janela de Contexto e Tokens](#9-janela-de-contexto-e-tokens)
10. [Prompt Systems](#10-prompt-systems)
11. [Developer Systems](#11-developer-systems)
12. [Guardrails, Segurança e Observabilidade](#12-guardrails-segurança-e-observabilidade)
13. [Persistência e Infraestrutura](#13-persistência-e-infraestrutura)
14. [Configuração e Variáveis de Ambiente](#14-configuração-e-variáveis-de-ambiente)
15. [Interfaces e Contratos (Schemas)](#15-interfaces-e-contratos-schemas)
16. [Roadmap e Extensões Futuras](#16-roadmap-e-extensões-futuras)

---

# 1. Visão Geral e Objetivos

A jClaw é uma plataforma open-core em Python para construção, orquestração e operação de agentes de IA conversacionais. Ela fornece primitivas de primeira classe para memória de sessão, handoffs entre agentes, roteamento multi-LLM, skills modulares e entrega em canais como Telegram e WhatsApp.

## 1.1 Princípios de Design

- **Convention over Configuration:** Defaults inteligentes; o desenvolvedor só configura o que precisa mudar.
- **Pluggable Everything:** Cada subsistema (LLM, memória, canal, skill) é uma interface abstrata com implementações trocáveis.
- **Observability-first:** Cada chamada de LLM, handoff e mutação de memória emite eventos estruturados para tracing (OpenTelemetry).
- **Async-native:** Construída sobre asyncio; suporta milhares de sessões concorrentes sem threads.
- **Type-safe:** Contratos definidos via Pydantic v2; validação em runtime e geração de JSON Schema.
- **Prompt-as-Code:** System prompts são artefatos versionados, testáveis e compostos por camadas reutilizáveis.
- **Developer-first DX:** CLI poderosa, hot-reload, playground interativo e documentação auto-gerada.

## 1.2 Stack Tecnológico Recomendado

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Runtime | Python 3.11+ / uvloop | Suporte nativo a async; performance I/O |
| Framework HTTP | FastAPI + Uvicorn | Webhooks dos canais e API de admin |
| Validação | Pydantic v2 | Schemas tipados, JSON Schema automático |
| Fila de Mensagens | Redis Streams / RabbitMQ | Desacoplamento entre canal e engine |
| Persistência | PostgreSQL 16 + pgvector | Histórico, memória semântica |
| Cache | Redis 7+ | Sessões ativas, rate limiting |
| Observabilidade | OpenTelemetry + Prometheus | Tracing distribuído, métricas |
| Templates | Jinja2 | Engine de templates para prompts |
| Container | Docker + Docker Compose | Ambiente reproduzível |
| CLI | Click + Rich | Developer tooling |

---

# 2. Arquitetura da Plataforma

## 2.1 Diagrama de Componentes (visão lógica)

```
┌────────────────────────────────────────────────────────────┐
│                     CANAIS (Inbound/Outbound)              │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│   │  Telegram   │  │  WhatsApp  │  │    REST    │  │ WebSocket│ │
│   └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
└────────────────────────────────────────────────────────────┘
                          │  Message Bus  │
┌────────────────────────────────────────────────────────────┐
│                     CORE ENGINE                            │
│   ┌─────────────────┐  ┌──────────────────────────────────┐│
│   │   Orchestrator   │  │ Agent Registry + Handoff Router ││
│   └─────────────────┘  └──────────────────────────────────┘│
│   ┌─────────────────┐  ┌─────────────┐  ┌────────────────┐│
│   │  Session Memory  │  │ LLM Router  │  │ Skill Executor ││
│   └─────────────────┘  └─────────────┘  └────────────────┘│
│   ┌─────────────────┐  ┌──────────────────────────────────┐│
│   │  Prompt Engine   │  │     Developer Systems (CLI)     ││
│   └─────────────────┘  └──────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
                              │
┌────────────────────────────────────────────────────────────┐
│                     PERSISTÊNCIA                           │
│   ┌────────────┐  ┌────────────┐  ┌─────────────────────┐ │
│   │ PostgreSQL │  │   Redis    │  │  Object Storage (S3) │ │
│   └────────────┘  └────────────┘  └─────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## 2.2 Estrutura de Diretórios do Projeto

```
jclaw/
├── core/
│   ├── orchestrator.py      # Loop principal do agente
│   ├── agent.py             # Classe base Agent
│   ├── handoff.py           # Motor de handoffs
│   ├── memory.py            # SessionMemory + MemoryStore
│   └── context_window.py    # Gerenciador de janela de contexto
├── llm/
│   ├── base.py              # LLMProvider ABC
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── groq_provider.py
│   └── router.py            # Roteamento dinâmico de modelos
├── prompts/
│   ├── engine.py            # PromptEngine — renderização e composição
│   ├── registry.py          # PromptRegistry — descoberta e versionamento
│   ├── layers.py            # Sistema de camadas (PromptLayer)
│   ├── variables.py         # PromptVariable — tipagem e validação
│   ├── pipelines.py         # PromptPipeline — transformações encadeadas
│   ├── testing.py           # PromptTestRunner — framework de testes
│   ├── templates/           # Templates Jinja2 base
│   │   ├── base_system.j2
│   │   ├── persona.j2
│   │   ├── guardrails.j2
│   │   └── output_format.j2
│   └── versions/            # Histórico de prompts versionados
├── skills/
│   ├── base.py              # Skill ABC
│   ├── registry.py          # Descoberta e registro
│   └── builtin/             # Skills nativas
├── channels/
│   ├── base.py              # ChannelAdapter ABC
│   ├── telegram.py
│   ├── whatsapp.py
│   └── rest.py
├── guardrails/
│   ├── input_filter.py
│   └── output_filter.py
├── storage/
│   ├── postgres.py
│   ├── redis_store.py
│   └── migrations/
├── config/
│   ├── settings.py          # Pydantic Settings
│   └── agents.yaml          # Definição declarativa de agentes
├── dev/
│   ├── cli.py               # CLI principal (jclaw)
│   ├── playground.py        # Playground interativo
│   ├── scaffold.py          # Gerador de código (scaffolding)
│   ├── inspector.py         # Debug inspector de agentes
│   ├── hot_reload.py        # Hot-reload para desenvolvimento
│   └── docs_generator.py    # Geração automática de docs
├── observability/
│   ├── tracing.py
│   └── metrics.py
└── tests/
    ├── prompts/             # Testes de prompts (prompt evals)
    └── agents/              # Testes de integração de agentes
```

---

# 3. Core Engine — Orquestrador de Agentes

## 3.1 Definição de Agente

Cada agente é uma unidade autônoma de raciocínio com identidade, instruções, modelo LLM designado e conjunto de skills. A classe base garante uma interface unificada.

**AgentConfig (Pydantic model)**

```python
class AgentConfig(BaseModel):
    agent_id: str                         # Identificador único
    name: str                             # Nome legível
    description: str                      # O que esse agente faz
    system_prompt: str | PromptRef        # Instruções diretas OU referência a prompt template
    llm_model: str = "claude-sonnet-4-20250514"
    llm_provider: str = "anthropic"       # Chave do provider
    temperature: float = 0.7
    max_tokens: int = 4096               # Limite de tokens de saída
    context_window: int = 128000         # Tamanho da janela
    skills: list[str] = []               # IDs das skills habilitadas
    handoff_targets: list[str] = []      # Agentes para os quais pode transferir
    guardrails: GuardrailConfig = GuardrailConfig()
    prompt_config: PromptConfig | None = None  # Configuração avançada de prompt
    metadata: dict[str, Any] = {}
```

## 3.2 Ciclo de Vida de uma Mensagem

1. Canal recebe mensagem do usuário e publica no Message Bus.
2. Orchestrator consome o evento, carrega a sessão e identifica o agente ativo.
3. Input Guardrails avaliam a mensagem (PII, conteúdo proibido, injection).
4. **Prompt Engine** resolve o system prompt: renderiza template, aplica camadas, injeta variáveis dinâmicas.
5. Context Window Manager monta o prompt final: system renderizado + memória + histórico + mensagem.
6. LLM Router envia para o provider/modelo configurado no agente.
7. Resposta é parseada: se contém tool_calls, o Skill Executor processa.
8. Se skill retorna handoff_request, o Handoff Router transfere para outro agente.
9. Output Guardrails validam a resposta final.
10. Session Memory persiste o turno (user + assistant).
11. Resposta é enviada de volta ao canal de origem.
12. **Prompt Analytics** registra métricas do prompt utilizado (versão, tokens, latência, qualidade).

---

# 4. Sistema de Memória de Sessão

A memória de sessão é o mecanismo que mantém o estado da conversação e informações extraídas ao longo do tempo. A jClaw implementa três camadas de memória que operam em conjunto.

## 4.1 Camadas de Memória

| Camada | Escopo | TTL Padrão | Storage | Descrição |
|---|---|---|---|---|
| Short-term | Turno atual | Dur. da req. | In-memory | Buffer das mensagens do turno corrente |
| Session | Conversação | 24h (config.) | Redis | Histórico de mensagens da sessão ativa |
| Long-term | Usuário | Indefinido | PostgreSQL | Fatos extraídos, preferências, resumos |

## 4.2 SessionMemory — Interface

```python
class SessionMemory(ABC):
    async def get_messages(self, session_id: str,
                           limit: int = 50) -> list[Message]:
        """Retorna histórico paginado da sessão."""

    async def add_message(self, session_id: str,
                          message: Message) -> None:
        """Adiciona mensagem ao histórico."""

    async def get_summary(self, session_id: str) -> str | None:
        """Retorna resumo compactado dos turnos antigos."""

    async def set_metadata(self, session_id: str,
                           key: str, value: Any) -> None:
        """Armazena metadado extraído (ex: nome do usuário)."""

    async def get_metadata(self, session_id: str,
                           key: str) -> Any:
        """Recupera metadado."""

    async def expire(self, session_id: str,
                     ttl_seconds: int) -> None:
        """Define TTL para a sessão."""
```

## 4.3 Estratégias de Compactação

Quando o histórico excede o limite de tokens da janela de contexto, a jClaw aplica uma das estratégias configuradas:

- **sliding_window:** Mantém as N mensagens mais recentes; descarta as mais antigas.
- **summarize_and_trim:** Gera um resumo das mensagens antigas via LLM e mantém o resumo + mensagens recentes.
- **semantic_pruning:** Usa embeddings para manter apenas as mensagens semanticamente relevantes para o turno atual.
- **hybrid:** Combina resumo + pruning semântico (padrão recomendado).

**Configuração por Agente**

```python
class MemoryConfig(BaseModel):
    strategy: Literal["sliding_window", "summarize_and_trim",
                       "semantic_pruning", "hybrid"] = "hybrid"
    max_messages: int = 100
    max_tokens: int = 8000        # Tokens reservados para memória
    summary_model: str = "claude-haiku-4-5-20251001"
    summary_max_tokens: int = 500
    ttl_seconds: int = 86400      # 24h
    persist_to_long_term: bool = True
```

---

# 5. Handoffs entre Agentes

Handoffs permitem que um agente transfira o controle da conversação para outro agente mais especializado. Este mecanismo é central na construção de fluxos multi-agente.

## 5.1 Modelo de Handoff

```python
class HandoffRequest(BaseModel):
    source_agent_id: str
    target_agent_id: str
    reason: str                       # Motivo legível da transferência
    context_payload: dict[str, Any] = {}  # Dados a passar para o próximo agente
    preserve_history: bool = True     # Manter histórico na sessão
    mode: Literal["transfer", "delegate", "escalate"] = "transfer"
```

## 5.2 Modos de Handoff

| Modo | Comportamento | Retorno? |
|---|---|---|
| transfer | Controle total passa para o agente destino. O agente origem sai do loop. | Não |
| delegate | Agente destino processa e devolve resultado ao agente origem, que continua. | Sim |
| escalate | Transferência com flag de escalation; pode notificar humano ou supervisor. | Não |

## 5.3 Handoff Router

O router valida se o handoff é permitido (via `handoff_targets` do agente de origem), executa hooks de pre/post transferência e gerencia a troca de contexto na sessão.

```python
class HandoffRouter:
    async def execute(self, request: HandoffRequest,
                      session: SessionMemory) -> HandoffResult:
        # 1. Validar permissão
        self._validate_target(request.source_agent_id,
                              request.target_agent_id)
        # 2. Executar pre-hooks
        await self._run_hooks("pre_handoff", request)
        # 3. Persistir contexto de handoff na sessão
        await session.set_metadata(
            request.source_agent_id,
            "last_handoff", request.model_dump()
        )
        # 4. Trocar agente ativo
        await session.set_metadata(
            "_system", "active_agent", request.target_agent_id
        )
        # 5. Executar post-hooks
        await self._run_hooks("post_handoff", request)
```

## 5.4 Handoff via Tool Call

Agentes solicitam handoffs retornando uma tool call especial que o Orchestrator intercepta:

```json
{
  "name": "handoff_to_agent",
  "description": "Transfere a conversa para outro agente",
  "input_schema": {
    "type": "object",
    "properties": {
      "target_agent_id": { "type": "string" },
      "reason": { "type": "string" },
      "context": { "type": "object" }
    },
    "required": ["target_agent_id", "reason"]
  }
}
```

---

# 6. Suporte Multi-LLM

A jClaw abstrai o acesso a múltiplos provedores de LLM através de uma interface unificada e um router inteligente que permite trocar modelos por agente, por tarefa ou por política de fallback.

## 6.1 LLMProvider — Interface Abstrata

```python
class LLMProvider(ABC):
    provider_id: str

    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[ToolDefinition] | None = None,
        stop_sequences: list[str] | None = None,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        ...

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        ...
```

## 6.2 Providers Suportados

| Provider | Modelos de Referência | Características |
|---|---|---|
| Anthropic | claude-opus-4, claude-sonnet-4, claude-haiku-4-5 | Tool use nativo, janelas até 200k tokens |
| OpenAI | gpt-4o, gpt-4o-mini, o3 | Function calling, vision |
| Google | gemini-2.5-pro, gemini-2.5-flash | Janelas de 1M+ tokens, multimodal |
| Groq | llama-3.3-70b, mixtral-8x7b | Latência ultra-baixa, custo reduzido |
| Ollama (local) | Qualquer modelo GGUF | Privácia total, sem custo de API |

## 6.3 LLM Router — Políticas de Roteamento

- **static:** Cada agente usa o modelo definido na sua configuração (padrão).
- **cost_optimized:** Usa modelo mais barato que atende o threshold de capacidade (ex: haiku para FAQ, sonnet para raciocínio).
- **latency_optimized:** Prioriza providers com menor latência medida no P95.
- **fallback_chain:** Tenta provider primário; em caso de erro/timeout, cai para o próximo na cadeia.

**Configuração do Router**

```python
class LLMRouterConfig(BaseModel):
    policy: Literal["static", "cost_optimized",
                     "latency_optimized", "fallback_chain"]
    fallback_chain: list[ProviderModelPair] = []
    timeout_seconds: float = 30.0
    max_retries: int = 2
    retry_delay_seconds: float = 1.0
    circuit_breaker: CircuitBreakerConfig = CircuitBreakerConfig()
```

**Circuit Breaker**

Cada provider possui um circuit breaker independente que abre após N falhas consecutivas, impedindo chamadas desnecessárias a um serviço indisponível.

```python
class CircuitBreakerConfig(BaseModel):
    failure_threshold: int = 5     # Falhas para abrir o circuito
    recovery_timeout: int = 60     # Segundos até tentar recovery
    half_open_max_calls: int = 2   # Chamadas de teste em half-open
```

---

# 7. Sistema de Skills

Skills são capacidades modulares que estendem os agentes além do texto. Cada skill expõe uma ou mais tools que o LLM pode chamar durante a conversação. O sistema de skills da jClaw é inspirado na abordagem tool-use das APIs de LLM, mas adiciona camadas de registro, permissão e execução segura.

## 7.1 Skill — Interface Base

```python
class Skill(ABC):
    skill_id: str
    name: str
    description: str
    version: str = "1.0.0"

    @abstractmethod
    def get_tools(self) -> list[ToolDefinition]:
        """Retorna definições de tools para o LLM."""

    @abstractmethod
    async def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        context: SkillContext
    ) -> ToolResult:
        """Executa a tool chamada pelo LLM."""

    def validate_input(
        self, tool_name: str, tool_input: dict
    ) -> bool:
        """Validação pré-execução."""
        return True
```

## 7.2 Skill Registry

O registry descobre skills automaticamente via entry_points (setuptools) ou via scan de diretório. Cada skill é registrada com suas tools e permissões.

```python
class SkillRegistry:
    def register(self, skill: Skill) -> None: ...
    def get_skill(self, skill_id: str) -> Skill: ...
    def get_tools_for_agent(
        self, agent_config: AgentConfig
    ) -> list[ToolDefinition]: ...
    def discover_plugins(self) -> None:
        """Auto-descobre skills via entry_points."""
```

## 7.3 Skills Nativas (Built-in)

| Skill | Tools | Descrição |
|---|---|---|
| web_search | search_web, fetch_url | Busca na web e extração de conteúdo |
| knowledge_base | query_kb, upsert_kb | Consulta e alimenta base vetorial (RAG) |
| calendar | list_events, create_event | Integração com calendários |
| database_query | run_sql, describe_tables | Consultas SQL controladas |
| code_executor | run_python, run_js | Execução sandboxed de código |
| file_manager | upload, download, list_files | Gestão de arquivos |
| handoff_to_agent | handoff_to_agent | Skill reservada para handoffs |

## 7.4 Criação de Skills Customizadas

Desenvolvedores podem criar skills como pacotes Python independentes que se conectam à plataforma via entry_points:

```python
# minha_skill/skill.py
from jclaw.skills.base import Skill, ToolDefinition, ToolResult

class MinhaSkill(Skill):
    skill_id = "minha_skill"
    name = "Minha Skill Customizada"
    description = "Faz algo específico do meu domínio"

    def get_tools(self) -> list[ToolDefinition]:
        return [ToolDefinition(
            name="minha_action",
            description="Executa minha ação customizada",
            input_schema={...}
        )]

    async def execute(self, tool_name, tool_input, ctx):
        result = await self._do_something(tool_input)
        return ToolResult(output=result)

# pyproject.toml
[project.entry-points."jclaw.skills"]
minha_skill = "minha_skill.skill:MinhaSkill"
```

---

# 8. Canais de Comunicação (Telegram / WhatsApp)

Canais são adaptadores que conectam o Core Engine a plataformas de mensageria externas. Cada canal implementa a interface ChannelAdapter, que normaliza mensagens de entrada e formata respostas de saída.

## 8.1 ChannelAdapter — Interface

```python
class ChannelAdapter(ABC):
    channel_id: str

    @abstractmethod
    async def receive_webhook(self, request: Request) -> InboundMessage:
        """Parseia webhook do canal em mensagem normalizada."""

    @abstractmethod
    async def send_message(
        self, chat_id: str, message: OutboundMessage
    ) -> None:
        """Envia resposta formatada para o canal."""

    @abstractmethod
    async def send_typing_indicator(self, chat_id: str) -> None:
        """Mostra indicador de digitação."""

    def get_session_id(
        self, inbound: InboundMessage
    ) -> str:
        """Gera session_id a partir do chat_id e channel_id."""
        return f"{self.channel_id}:{inbound.chat_id}"
```

## 8.2 Telegram

**Configuração**

```python
class TelegramConfig(BaseModel):
    bot_token: SecretStr
    webhook_url: str                     # URL pública do webhook
    webhook_secret: str                  # Token de verificação
    allowed_updates: list[str] = ["message", "callback_query"]
    parse_mode: str = "MarkdownV2"
    max_message_length: int = 4096       # Limite do Telegram
```

**Características**

- Suporte a Inline Keyboards para interação rica (botões, menus).
- Envio de documentos, imagens e áudios como mídia nativa.
- Comandos (`/start`, `/help`, `/reset`) mapeados para ações do orquestrador.
- Resposta automática a `callback_query` com `answer_callback_query`.
- Split automático de mensagens longas respeitando o limite de 4096 chars.

## 8.3 WhatsApp (via Meta Cloud API)

**Configuração**

```python
class WhatsAppConfig(BaseModel):
    phone_number_id: str
    access_token: SecretStr
    verify_token: str
    webhook_url: str
    api_version: str = "v21.0"
    business_account_id: str
    max_message_length: int = 4096
    template_namespace: str | None = None  # Para HSMs
```

**Características**

- Recepção e envio de texto, imagens, documentos e áudio.
- Suporte a mensagens interativas (botões, listas, reply buttons).
- Controle de janela de 24h: mensagens de template (HSM) fora da janela.
- Leitura de status de entrega (sent, delivered, read).
- Rate limiting com backoff exponencial.
- Verificação de assinatura HMAC-SHA256 nos webhooks.

## 8.4 Modelo de Mensagem Normalizada

```python
class InboundMessage(BaseModel):
    message_id: str
    chat_id: str
    user_id: str
    channel: str                # "telegram" | "whatsapp" | "rest"
    content_type: Literal["text", "image", "audio",
                           "document", "location"]
    text: str | None = None
    media_url: str | None = None
    metadata: dict[str, Any] = {}
    timestamp: datetime

class OutboundMessage(BaseModel):
    text: str | None = None
    media: list[MediaAttachment] = []
    buttons: list[Button] = []
    metadata: dict[str, Any] = {}
```

---

# 9. Janela de Contexto e Tokens

O gerenciamento inteligente da janela de contexto é crítico para a qualidade das respostas e o controle de custos. A jClaw parametriza todos os limites e oferece estratégias automáticas de compactação.

## 9.1 Orçamento de Tokens

A janela de contexto é dividida em regiões com orçamentos fixos ou percentuais:

| Região | Descrição | Padrão | Configurável? |
|---|---|---|---|
| system_prompt | Instruções do agente + skill descriptions | Calculado | Sim |
| prompt_layers | Camadas adicionais de prompt (persona, guardrails, formato) | Calculado | Sim |
| memory_slot | Resumos e fatos de longo prazo | 2000 tokens | Sim |
| history_slot | Histórico de mensagens da sessão | Restante disponível | Sim |
| user_message | Mensagem atual do usuário | Ilimitado (entrada) | Não |
| response_budget | Tokens reservados para a resposta do LLM | max_tokens do agente | Sim |
| safety_margin | Margem de segurança para evitar truncamento | 500 tokens | Sim |

## 9.2 ContextWindowManager

```python
class ContextWindowManager:
    def __init__(self, agent_config: AgentConfig,
                 token_counter: TokenCounter,
                 prompt_engine: PromptEngine):
        self.max_context = agent_config.context_window
        self.max_response = agent_config.max_tokens
        self.counter = token_counter
        self.prompt_engine = prompt_engine

    def build_prompt(
        self,
        system: str,
        memory_facts: list[str],
        history: list[Message],
        user_message: Message,
        tools: list[ToolDefinition],
    ) -> PromptPayload:
        budget = self.max_context - self.max_response - SAFETY_MARGIN
        system_tokens = self.counter.count(system)
        tools_tokens = self.counter.count_tools(tools)
        user_tokens = self.counter.count_message(user_message)

        remaining = budget - system_tokens - tools_tokens - user_tokens
        memory_budget = min(remaining * 0.2, 2000)
        history_budget = remaining - memory_budget

        # Compactar histórico se necessário
        trimmed_history = self._fit_history(
            history, int(history_budget)
        )
        ...
```

## 9.3 Token Counter

Cada provider implementa contagem específica. Para Anthropic, usa-se a API de contagem nativa. Para OpenAI, tiktoken. Para modelos locais, sentencepiece ou HuggingFace tokenizers.

```python
class TokenCounter(ABC):
    @abstractmethod
    def count(self, text: str) -> int: ...

    @abstractmethod
    def count_messages(self, messages: list[Message]) -> int: ...

    @abstractmethod
    def count_tools(
        self, tools: list[ToolDefinition]
    ) -> int: ...
```

---

# 10. Prompt Systems

O Prompt System é o subsistema responsável por gerenciar, compor, versionar e testar os system prompts utilizados pelos agentes. Na jClaw, prompts são tratados como artefatos de engenharia — versionados, testáveis, compostos por camadas e parametrizados por variáveis dinâmicas.

## 10.1 Filosofia: Prompt-as-Code

Diferente da abordagem de strings hardcoded, a jClaw trata prompts como código:

- **Versionados:** Cada prompt possui um identificador semântico e uma versão (semver). Alterações geram novas versões rastreáveis.
- **Compostos por camadas:** Um system prompt final é a composição de múltiplas camadas reutilizáveis (persona, guardrails, formato de saída, contexto de domínio).
- **Parametrizados:** Variáveis dinâmicas são resolvidas em runtime com base no contexto da sessão, no canal, no usuário ou em dados externos.
- **Testáveis:** Prompts possuem suítes de teste (prompt evals) que validam comportamento esperado antes do deploy.
- **Observáveis:** Cada renderização de prompt emite métricas de tokens consumidos, versão utilizada e tempo de resolução.

## 10.2 PromptTemplate — Modelo Base

```python
class PromptTemplate(BaseModel):
    template_id: str                          # Identificador único (ex: "vendas.system.v2")
    name: str                                 # Nome legível
    description: str                          # O que esse template faz
    version: str = "1.0.0"                    # Versionamento semântico
    engine: Literal["jinja2", "f-string",
                     "mustache"] = "jinja2"   # Engine de renderização
    content: str                              # Template com placeholders
    variables: list[PromptVariable] = []      # Variáveis esperadas
    metadata: dict[str, Any] = {}
    tags: list[str] = []                      # Tags para busca e categorização
    created_at: datetime = Field(default_factory=datetime.utcnow)
    parent_id: str | None = None              # Template pai (herança)
```

## 10.3 Variáveis de Prompt

Variáveis são placeholders tipados e validados que são resolvidos antes da renderização. Cada variável possui um tipo, valor default e resolver opcional.

```python
class PromptVariable(BaseModel):
    name: str                                 # Nome da variável no template
    var_type: Literal["string", "int", "float",
                       "bool", "list", "dict",
                       "datetime", "json"] = "string"
    required: bool = True
    default: Any = None
    description: str = ""
    resolver: str | None = None               # Callable path para resolução dinâmica
    validation: VariableValidation | None = None

class VariableValidation(BaseModel):
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None                # Regex
    enum: list[str] | None = None             # Valores permitidos
    max_tokens: int | None = None             # Limite de tokens da variável
```

**Resolvers Dinâmicos**

Resolvers são funções que calculam o valor de uma variável em runtime com base no contexto:

```python
class VariableResolverRegistry:
    """Registro de resolvers para variáveis de prompt."""

    _resolvers: dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        self._resolvers[name] = fn

    async def resolve(self, name: str,
                      context: PromptContext) -> Any:
        resolver = self._resolvers[name]
        return await resolver(context)

# Resolvers nativos
@resolver("user_name")
async def resolve_user_name(ctx: PromptContext) -> str:
    return await ctx.session.get_metadata(ctx.session_id, "user_name") or "Usuário"

@resolver("current_datetime")
async def resolve_current_datetime(ctx: PromptContext) -> str:
    return datetime.now(ctx.timezone).strftime("%d/%m/%Y %H:%M")

@resolver("user_language")
async def resolve_user_language(ctx: PromptContext) -> str:
    return ctx.inbound_message.metadata.get("language", "pt-BR")

@resolver("channel_constraints")
async def resolve_channel_constraints(ctx: PromptContext) -> str:
    constraints = {
        "telegram": "Respostas com no máximo 4096 caracteres. Use MarkdownV2.",
        "whatsapp": "Respostas com no máximo 4096 caracteres. Sem markdown complexo.",
        "rest": "Sem restrições de formato.",
    }
    return constraints.get(ctx.channel, "")

@resolver("active_skills_description")
async def resolve_active_skills(ctx: PromptContext) -> str:
    tools = ctx.skill_registry.get_tools_for_agent(ctx.agent_config)
    return "\n".join(f"- {t.name}: {t.description}" for t in tools)
```

## 10.4 Sistema de Camadas (Prompt Layers)

Um system prompt final é a composição ordenada de múltiplas camadas. Cada camada tem uma prioridade e pode ser condicional.

```python
class PromptLayer(BaseModel):
    layer_id: str
    name: str
    priority: int = 0                         # Menor = primeiro na composição
    template: str | PromptTemplate            # Conteúdo ou referência
    condition: str | None = None              # Expressão condicional (ex: "channel == 'whatsapp'")
    separator: str = "\n\n"                   # Separador entre camadas
    required: bool = True                     # Se False, falha silenciosa
    max_tokens: int | None = None             # Budget máximo dessa camada

class PromptLayerStack(BaseModel):
    """Pilha ordenada de camadas que compõe o system prompt final."""
    layers: list[PromptLayer]

    def resolve(self, context: PromptContext) -> list[PromptLayer]:
        """Filtra camadas com condição atendida e ordena por prioridade."""
        active = [l for l in self.layers if self._eval_condition(l, context)]
        return sorted(active, key=lambda l: l.priority)
```

**Camadas Padrão**

| Camada | Prioridade | Descrição |
|---|---|---|
| `identity` | 0 | Quem é o agente: nome, papel, empresa |
| `persona` | 10 | Tom de voz, estilo, idioma, personalidade |
| `domain_knowledge` | 20 | Conhecimento específico do domínio / FAQs |
| `guardrails` | 30 | Restrições: o que NÃO fazer, limites de atuação |
| `output_format` | 40 | Formato esperado da resposta (JSON, markdown, texto livre) |
| `tools_context` | 50 | Instruções de uso das tools disponíveis |
| `channel_adapter` | 60 | Regras específicas do canal (Telegram, WhatsApp) |
| `memory_context` | 70 | Fatos do usuário e resumo da conversa |
| `temporal_context` | 80 | Data/hora atual, timezone, eventos relevantes |
| `custom` | 90+ | Camadas customizadas do desenvolvedor |

**Exemplo de Composição em YAML**

```yaml
prompt_layers:
  - layer_id: identity
    name: "Identidade"
    priority: 0
    template: |
      Você é {{ agent_name }}, assistente virtual da {{ company_name }}.
      Seu papel é {{ agent_description }}.

  - layer_id: persona
    name: "Persona"
    priority: 10
    template: "prompts/templates/persona.j2"   # Referência a arquivo

  - layer_id: guardrails_channel
    name: "Regras do Canal"
    priority: 60
    condition: "channel == 'whatsapp'"
    template: |
      REGRAS DO WHATSAPP:
      - Respostas com no máximo 4096 caracteres.
      - Não use formatação markdown complexa.
      - Prefira listas simples com hífens.
      - Indique quando uma resposta será dividida em partes.

  - layer_id: temporal
    name: "Contexto Temporal"
    priority: 80
    template: |
      Data e hora atual: {{ current_datetime }}.
      Timezone do usuário: {{ user_timezone }}.
```

## 10.5 PromptEngine — Motor de Renderização

O PromptEngine é o componente central que recebe um AgentConfig, resolve as camadas, injeta variáveis e produz o system prompt final renderizado.

```python
class PromptEngine:
    def __init__(
        self,
        template_registry: PromptRegistry,
        variable_resolvers: VariableResolverRegistry,
        token_counter: TokenCounter,
    ):
        self.registry = template_registry
        self.resolvers = variable_resolvers
        self.counter = token_counter
        self._jinja_env = Environment(
            loader=FileSystemLoader("prompts/templates"),
            undefined=StrictUndefined,
        )

    async def render(
        self,
        agent_config: AgentConfig,
        context: PromptContext,
    ) -> RenderedPrompt:
        """Renderiza o system prompt completo do agente."""

        # 1. Resolver camadas ativas
        layers = agent_config.prompt_config.layers.resolve(context)

        # 2. Resolver variáveis dinâmicas
        variables = await self._resolve_variables(
            agent_config.prompt_config.variables, context
        )

        # 3. Renderizar cada camada
        rendered_parts = []
        for layer in layers:
            template = self._get_template(layer)
            rendered = template.render(**variables)

            # Truncar se exceder budget da camada
            if layer.max_tokens:
                rendered = self._truncate_to_tokens(
                    rendered, layer.max_tokens
                )
            rendered_parts.append(rendered)

        # 4. Compor prompt final
        final_prompt = "\n\n".join(rendered_parts)

        # 5. Emitir métricas
        token_count = self.counter.count(final_prompt)

        return RenderedPrompt(
            content=final_prompt,
            token_count=token_count,
            layers_used=[l.layer_id for l in layers],
            variables_resolved=list(variables.keys()),
            template_version=agent_config.prompt_config.version,
        )

class RenderedPrompt(BaseModel):
    content: str
    token_count: int
    layers_used: list[str]
    variables_resolved: list[str]
    template_version: str
    rendered_at: datetime = Field(default_factory=datetime.utcnow)
```

## 10.6 PromptRegistry — Versionamento e Descoberta

```python
class PromptRegistry:
    """Registro central de templates de prompt."""

    async def register(self, template: PromptTemplate) -> None:
        """Registra um novo template ou nova versão."""

    async def get(self, template_id: str,
                  version: str | None = None) -> PromptTemplate:
        """Recupera template por ID. Se version=None, retorna a mais recente."""

    async def list_versions(self, template_id: str) -> list[str]:
        """Lista todas as versões de um template."""

    async def diff(self, template_id: str,
                   version_a: str, version_b: str) -> PromptDiff:
        """Compara duas versões de um template."""

    async def rollback(self, template_id: str,
                       target_version: str) -> None:
        """Reverte para uma versão anterior."""

    async def search(self, query: str,
                     tags: list[str] | None = None) -> list[PromptTemplate]:
        """Busca templates por texto ou tags."""
```

**Persistência de Prompts (PostgreSQL)**

```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    engine VARCHAR(20) DEFAULT 'jinja2',
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    tags TEXT[] DEFAULT '{}',
    parent_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(template_id, version)
);

CREATE TABLE prompt_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    agent_id VARCHAR(100),
    session_id UUID,
    tokens_used INT,
    render_time_ms FLOAT,
    layers_used TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 10.7 Prompt Pipelines — Transformações Encadeadas

Pipelines permitem aplicar transformações sequenciais ao prompt antes do envio ao LLM. Cada step é um `PromptTransformer` que recebe e retorna texto.

```python
class PromptTransformer(ABC):
    """Transformação atômica em um prompt."""

    @abstractmethod
    async def transform(self, content: str,
                        context: PromptContext) -> str: ...

class PromptPipeline:
    """Cadeia de transformações aplicadas ao prompt renderizado."""

    def __init__(self, steps: list[PromptTransformer]):
        self.steps = steps

    async def execute(self, content: str,
                      context: PromptContext) -> str:
        result = content
        for step in self.steps:
            result = await step.transform(result, context)
        return result
```

**Transformers Nativos**

| Transformer | Descrição |
|---|---|
| `StripWhitespace` | Remove espaços em branco excessivos e linhas vazias |
| `InjectMemoryFacts` | Insere fatos do usuário no ponto marcado com `{{ memory_facts }}` |
| `TokenBudgetEnforcer` | Trunca seções que excedam o budget alocado |
| `LanguageAdapter` | Traduz instruções estáticas para o idioma do usuário |
| `PIIRedactor` | Remove dados sensíveis antes de enviar ao LLM |
| `ConditionalSectionRemover` | Remove blocos `{% if %}` cujas condições não foram atendidas |
| `PromptInjectionHardener` | Adiciona instruções anti-injection ao prompt |

## 10.8 Prompt Testing Framework

O jClaw oferece um framework de testes para validar prompts antes do deploy, garantindo que alterações não introduzam regressões.

```python
class PromptTestCase(BaseModel):
    """Caso de teste para um prompt."""
    test_id: str
    name: str
    description: str
    template_id: str
    variables: dict[str, Any] = {}           # Variáveis de entrada
    mock_context: MockPromptContext           # Contexto simulado
    assertions: list[PromptAssertion]        # Asserções a validar

class PromptAssertion(BaseModel):
    assertion_type: Literal[
        "contains",           # Prompt renderizado contém o texto
        "not_contains",       # Prompt renderizado NÃO contém o texto
        "max_tokens",         # Não excede N tokens
        "layer_present",      # Camada específica está ativa
        "layer_absent",       # Camada específica está ausente
        "matches_regex",      # Conteúdo corresponde a regex
        "variable_resolved",  # Variável foi resolvida com valor esperado
        "llm_eval",           # LLM avalia qualidade da saída (prompt eval)
    ]
    value: Any
    message: str = ""                        # Mensagem de erro customizada

class PromptTestRunner:
    """Executor de testes de prompt."""

    async def run_suite(self, suite: list[PromptTestCase]) -> TestReport:
        results = []
        for test in suite:
            result = await self._run_test(test)
            results.append(result)
        return TestReport(results=results)

    async def _run_test(self, test: PromptTestCase) -> TestResult:
        # Renderizar prompt com contexto mock
        rendered = await self.engine.render(
            agent_config=test.mock_context.agent_config,
            context=test.mock_context.to_prompt_context(),
        )
        # Validar asserções
        for assertion in test.assertions:
            passed = self._check_assertion(rendered, assertion)
            if not passed:
                return TestResult(test_id=test.test_id, passed=False,
                                  message=assertion.message)
        return TestResult(test_id=test.test_id, passed=True)
```

**Exemplo de Teste em YAML**

```yaml
prompt_tests:
  - test_id: vendas_system_prompt_basics
    name: "System prompt de vendas contém identidade"
    template_id: vendas.system
    variables:
      agent_name: "Agente de Vendas"
      company_name: "TechCorp"
    mock_context:
      channel: "whatsapp"
      agent_id: vendas
    assertions:
      - assertion_type: contains
        value: "TechCorp"
        message: "Prompt deve mencionar o nome da empresa"
      - assertion_type: contains
        value: "consultor de vendas"
        message: "Prompt deve declarar o papel do agente"
      - assertion_type: max_tokens
        value: 3000
        message: "System prompt não pode exceder 3000 tokens"
      - assertion_type: layer_present
        value: "guardrails_channel"
        message: "Camada de guardrails de canal deve estar ativa no WhatsApp"
      - assertion_type: not_contains
        value: "MarkdownV2"
        message: "WhatsApp não suporta MarkdownV2"

  - test_id: vendas_llm_eval_qualidade
    name: "LLM avalia qualidade da resposta com prompt de vendas"
    template_id: vendas.system
    variables:
      agent_name: "Agente de Vendas"
      company_name: "TechCorp"
    mock_context:
      channel: "telegram"
      agent_id: vendas
      user_message: "Quanto custa o plano premium?"
    assertions:
      - assertion_type: llm_eval
        value:
          eval_model: "claude-haiku-4-5-20251001"
          criteria: "O agente respondeu de forma profissional e informativa?"
          expected: true
        message: "Resposta deve ser avaliada como profissional pelo LLM"
```

## 10.9 Configuração Completa de Prompt no agents.yaml

```yaml
agents:
  - agent_id: vendas
    name: "Agente de Vendas"
    llm_provider: anthropic
    llm_model: claude-sonnet-4-20250514
    temperature: 0.7
    max_tokens: 4096
    context_window: 128000

    prompt_config:
      version: "2.1.0"
      variables:
        - name: company_name
          var_type: string
          default: "TechCorp"
        - name: current_datetime
          var_type: string
          resolver: "current_datetime"
        - name: user_name
          var_type: string
          resolver: "user_name"
          default: "Usuário"
        - name: channel_constraints
          var_type: string
          resolver: "channel_constraints"

      layers:
        - layer_id: identity
          priority: 0
          template: |
            Você é {{ agent_name }}, consultor de vendas virtual da {{ company_name }}.

        - layer_id: persona
          priority: 10
          template: |
            PERSONALIDADE:
            - Seja profissional, empático e orientado a soluções.
            - Use linguagem acessível, evite jargão técnico.
            - Sempre pergunte antes de assumir a necessidade do cliente.
            - Demonstre conhecimento dos produtos sem ser agressivo.

        - layer_id: domain
          priority: 20
          template: "prompts/vendas/domain_knowledge.j2"

        - layer_id: guardrails
          priority: 30
          template: |
            RESTRIÇÕES:
            - Nunca forneça informações falsas sobre preços ou disponibilidade.
            - Não faça promessas que a empresa não pode cumprir.
            - Se não souber a resposta, diga que vai verificar.
            - Não discuta concorrentes de forma negativa.
            - Nunca compartilhe dados internos da empresa.

        - layer_id: output_format
          priority: 40
          template: |
            FORMATO:
            - Respostas concisas (máximo 3 parágrafos).
            - Use bullet points para listas de benefícios.
            - Inclua CTA (call to action) quando apropriado.

        - layer_id: channel_whatsapp
          priority: 60
          condition: "channel == 'whatsapp'"
          template: |
            CANAL WHATSAPP:
            {{ channel_constraints }}
            - Use emojis com moderação para tornar a conversa amigável.
            - Ofereça botões de resposta rápida quando possível.

        - layer_id: temporal
          priority: 80
          template: |
            CONTEXTO:
            - Data atual: {{ current_datetime }}.
            - Nome do cliente: {{ user_name }}.

      pipeline:
        - StripWhitespace
        - InjectMemoryFacts
        - TokenBudgetEnforcer
        - PromptInjectionHardener
```

---

# 11. Developer Systems

O Developer Systems é o conjunto de ferramentas, APIs e abstrações que tornam produtiva a experiência do desenvolvedor ao criar, testar, debugar e operar agentes na jClaw. O objetivo é reduzir o ciclo de feedback entre ideia e agente funcional.

## 11.1 CLI — Interface de Linha de Comando

A jClaw oferece uma CLI poderosa construída com Click + Rich, expondo todas as operações da plataforma.

```
jclaw <command> [options]
```

**Comandos Principais**

| Comando | Descrição |
|---|---|
| `jclaw init` | Scaffolding de um novo projeto jClaw |
| `jclaw agent create <id>` | Gera estrutura de um novo agente |
| `jclaw agent list` | Lista agentes registrados |
| `jclaw agent inspect <id>` | Mostra configuração e estado do agente |
| `jclaw skill create <id>` | Gera estrutura de uma nova skill |
| `jclaw skill list` | Lista skills disponíveis |
| `jclaw prompt render <agent_id>` | Renderiza e exibe o system prompt final |
| `jclaw prompt diff <id> <v1> <v2>` | Diff entre versões de prompt |
| `jclaw prompt test [--suite path]` | Executa testes de prompt |
| `jclaw chat <agent_id>` | Inicia sessão interativa com um agente (playground) |
| `jclaw serve` | Inicia o servidor de desenvolvimento com hot-reload |
| `jclaw migrate` | Executa migrações de banco de dados |
| `jclaw config validate` | Valida `agents.yaml` e variáveis de ambiente |
| `jclaw docs generate` | Gera documentação automática da plataforma |
| `jclaw trace <session_id>` | Inspeciona trace completo de uma sessão |
| `jclaw bench <agent_id>` | Executa benchmark de latência e custo |

**Exemplo de Uso**

```bash
# Criar novo projeto
$ jclaw init meu-projeto
✓ Estrutura de diretórios criada
✓ agents.yaml gerado com agente de exemplo
✓ .env.example criado
✓ Docker Compose configurado
✓ Dependências instaladas

# Criar agente
$ jclaw agent create suporte \
    --provider anthropic \
    --model claude-sonnet-4-20250514 \
    --skills knowledge_base,handoff_to_agent
✓ Agente 'suporte' criado em config/agents.yaml
✓ Prompt template gerado em prompts/suporte/system.j2
✓ Testes de prompt criados em tests/prompts/suporte.yaml

# Renderizar prompt para debug
$ jclaw prompt render vendas --channel whatsapp --vars '{"company_name": "Acme"}'
╭──────────── System Prompt (vendas v2.1.0) ────────────╮
│ Layers: identity → persona → domain → guardrails →    │
│         output_format → channel_whatsapp → temporal    │
│ Tokens: 1,847 / 3,000 budget                          │
│ Variables: 4 resolved, 0 failed                        │
╰────────────────────────────────────────────────────────╯
Você é Agente de Vendas, consultor de vendas virtual da Acme.
[... prompt renderizado ...]

# Testar prompts
$ jclaw prompt test --suite tests/prompts/vendas.yaml
✓ vendas_system_prompt_basics       (4 assertions, 12ms)
✓ vendas_llm_eval_qualidade         (1 assertion, 2.3s)
✓ vendas_whatsapp_format            (3 assertions, 8ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 tests passed, 0 failed (2.32s)
```

## 11.2 Playground Interativo

O Playground é um ambiente local que simula a experiência do usuário final, permitindo testar agentes sem configurar canais externos.

```python
class Playground:
    """Ambiente de teste interativo para agentes."""

    def __init__(self, orchestrator: Orchestrator,
                 agent_id: str, channel: str = "playground"):
        self.orchestrator = orchestrator
        self.agent_id = agent_id
        self.channel = channel
        self.session_id = f"playground:{uuid4()}"

    async def chat(self, message: str) -> PlaygroundResponse:
        """Envia mensagem e retorna resposta com debug info."""
        inbound = InboundMessage(
            message_id=str(uuid4()),
            chat_id="playground",
            user_id="developer",
            channel=self.channel,
            content_type="text",
            text=message,
            timestamp=datetime.utcnow(),
        )
        response = await self.orchestrator.process(inbound)
        return PlaygroundResponse(
            text=response.text,
            agent_id=response.agent_id,
            model_used=response.model_used,
            tokens=response.usage,
            latency_ms=response.latency_ms,
            tool_calls=response.tool_calls,
            handoffs=response.handoffs,
            prompt_version=response.prompt_version,
            memory_state=await self._get_memory_state(),
        )

    async def simulate_channel(self, channel: str) -> None:
        """Altera canal simulado (telegram, whatsapp, rest)."""
        self.channel = channel

    async def reset(self) -> None:
        """Limpa sessão e memória."""
        self.session_id = f"playground:{uuid4()}"

    async def inject_memory(self, facts: dict[str, Any]) -> None:
        """Injeta fatos na memória para teste."""
        for key, value in facts.items():
            await self.orchestrator.memory.set_metadata(
                self.session_id, key, value
            )

class PlaygroundResponse(BaseModel):
    text: str
    agent_id: str
    model_used: str
    tokens: TokenUsage
    latency_ms: float
    tool_calls: list[ToolCall] = []
    handoffs: list[HandoffRequest] = []
    prompt_version: str
    memory_state: dict[str, Any] = {}
```

**Playground via CLI**

```bash
$ jclaw chat vendas --channel whatsapp
╭──────── jClaw Playground ────────╮
│ Agent:   vendas (v2.1.0)         │
│ Model:   claude-sonnet-4         │
│ Channel: whatsapp                │
│ Commands: /switch, /reset,       │
│   /memory, /trace, /prompt, /q   │
╰──────────────────────────────────╯

You > Olá, quais planos vocês têm?

vendas (claude-sonnet-4 | 847ms | 312 tokens) >
Olá! Temos três planos disponíveis...

You > /trace
╭──────── Trace do último turno ────────╮
│ Session:    playground:a1b2c3         │
│ Agent:      vendas                    │
│ Model:      claude-sonnet-4-20250514  │
│ Prompt:     vendas.system v2.1.0      │
│ Layers:     7 ativas                  │
│ Input:      142 tokens                │
│ Output:     312 tokens                │
│ Latency:    847ms                     │
│ Tools:      0 calls                   │
│ Handoffs:   0                         │
│ Guardrails: 2 passed, 0 blocked       │
│ Memory:     1 fact extracted           │
╰───────────────────────────────────────╯

You > /memory
╭──────── Memory State ────────╮
│ user_name: null               │
│ facts_extracted: 0            │
│ history_messages: 2           │
│ session_tokens: 454           │
╰───────────────────────────────╯
```

## 11.3 Scaffolding e Geração de Código

O sistema de scaffolding gera automaticamente a estrutura de novos componentes com código boilerplate, testes e documentação.

```python
class ScaffoldGenerator:
    """Gerador de código para novos componentes."""

    templates: dict[str, str] = {
        "agent": "templates/scaffold/agent.py.j2",
        "skill": "templates/scaffold/skill.py.j2",
        "channel": "templates/scaffold/channel.py.j2",
        "guardrail": "templates/scaffold/guardrail.py.j2",
        "prompt": "templates/scaffold/prompt.j2",
        "test": "templates/scaffold/test.py.j2",
    }

    def generate(self, component_type: str,
                 name: str, options: dict) -> list[GeneratedFile]:
        """Gera arquivos de scaffold para um componente."""
        ...
```

**Scaffolds Disponíveis**

| Comando | Arquivos Gerados |
|---|---|
| `jclaw agent create <id>` | `agents.yaml` entry, `prompts/<id>/system.j2`, `tests/prompts/<id>.yaml` |
| `jclaw skill create <id>` | `skills/<id>/skill.py`, `skills/<id>/tests.py`, `pyproject.toml` entry |
| `jclaw channel create <id>` | `channels/<id>.py`, `channels/<id>_test.py` |
| `jclaw guardrail create <id>` | `guardrails/<id>.py`, `guardrails/<id>_test.py` |
| `jclaw prompt create <id>` | `prompts/<id>/system.j2`, `prompts/<id>/test.yaml`, `prompts/<id>/CHANGELOG.md` |

## 11.4 Hot-Reload para Desenvolvimento

Durante o desenvolvimento, alterações em arquivos de configuração, prompts e skills são detectadas e aplicadas automaticamente sem reiniciar o servidor.

```python
class HotReloadWatcher:
    """Monitora alterações e recarrega componentes."""

    watch_patterns: list[str] = [
        "config/agents.yaml",
        "prompts/**/*.j2",
        "prompts/**/*.yaml",
        "skills/**/*.py",
        "guardrails/**/*.py",
    ]

    async def start(self) -> None:
        """Inicia watcher com watchfiles."""
        async for changes in awatch(*self.watch_patterns):
            for change_type, path in changes:
                await self._reload_component(change_type, path)

    async def _reload_component(self, change_type: str,
                                 path: str) -> None:
        if "agents.yaml" in path:
            await self.orchestrator.reload_agents()
            self._notify("Agents reloaded")
        elif path.endswith(".j2"):
            await self.prompt_engine.invalidate_cache(path)
            self._notify(f"Prompt template reloaded: {path}")
        elif "skills/" in path:
            await self.skill_registry.reload()
            self._notify("Skills reloaded")
```

**Ativação**

```bash
$ jclaw serve --reload
🔄 Hot-reload ativo. Monitorando alterações em:
   - config/agents.yaml
   - prompts/**/*.j2
   - skills/**/*.py
   - guardrails/**/*.py
```

## 11.5 Agent Inspector — Ferramenta de Debug

O Inspector permite inspecionar o estado interno de um agente em execução: sessões ativas, memória, prompts renderizados e histórico de decisões.

```python
class AgentInspector:
    """Ferramenta de inspeção e debug de agentes."""

    async def inspect_agent(self, agent_id: str) -> AgentInspection:
        """Retorna estado completo de um agente."""
        config = self.registry.get_agent(agent_id)
        sessions = await self.memory.get_active_sessions(agent_id)
        return AgentInspection(
            config=config,
            active_sessions=len(sessions),
            prompt_version=config.prompt_config.version,
            skills_loaded=[s.skill_id for s in
                          self.skill_registry.get_skills(agent_id)],
            llm_stats=await self._get_llm_stats(agent_id),
            guardrails_active=config.guardrails.enabled_rules,
        )

    async def inspect_session(self, session_id: str) -> SessionInspection:
        """Retorna estado completo de uma sessão."""
        return SessionInspection(
            messages=await self.memory.get_messages(session_id),
            metadata=await self.memory.get_all_metadata(session_id),
            active_agent=await self.memory.get_metadata(
                session_id, "_system:active_agent"
            ),
            handoff_history=await self._get_handoff_log(session_id),
            token_usage=await self._calculate_session_tokens(session_id),
            memory_facts=await self._get_user_facts(session_id),
        )

    async def replay_session(self, session_id: str,
                              from_turn: int = 0) -> list[ReplayStep]:
        """Re-executa uma sessão passo a passo para debug."""
        ...
```

**Inspector via CLI**

```bash
$ jclaw agent inspect vendas
╭──────── Agent: vendas ────────╮
│ Name:          Agente de Vendas│
│ Model:         claude-sonnet-4 │
│ Provider:      anthropic       │
│ Prompt:        v2.1.0          │
│ Skills:        3 loaded        │
│   - knowledge_base             │
│   - calendar                   │
│   - handoff_to_agent           │
│ Guardrails:    4 active        │
│ Active Sess.:  12              │
│ Avg Latency:   923ms (P95)     │
│ Token/turn:    ~450 avg        │
│ Cost/turn:     $0.0034 avg     │
╰────────────────────────────────╯

$ jclaw trace session:abc123
╭──────────── Session Trace ─────────────╮
│ Turn 1  [user]     "Olá"              │
│ Turn 2  [vendas]   "Olá! Como posso.."│
│          └─ 234 tok, 412ms             │
│ Turn 3  [user]     "Quero o plano pro"│
│ Turn 4  [vendas]   tool:query_kb       │
│          └─ KB: 3 results              │
│ Turn 5  [vendas]   "O Plano Pro..."   │
│          └─ 567 tok, 1.2s              │
│ Turn 6  [user]     "Preciso de suporte"│
│ Turn 7  [vendas]   handoff → suporte   │
│          └─ reason: "cliente pediu..."│
│ Turn 8  [suporte]  "Olá! Sou do..."   │
╰────────────────────────────────────────╯
```

## 11.6 Documentação Auto-Gerada

A jClaw gera documentação automaticamente a partir dos contratos Pydantic, das definições de agentes e dos metadados de skills/prompts.

```python
class DocsGenerator:
    """Gerador de documentação da plataforma."""

    async def generate(self, output_dir: str = "docs/") -> None:
        """Gera documentação completa."""
        # 1. API Reference (OpenAPI via FastAPI)
        await self._generate_openapi(output_dir)
        # 2. Agent Catalog
        await self._generate_agent_catalog(output_dir)
        # 3. Skill Reference
        await self._generate_skill_docs(output_dir)
        # 4. Prompt Library
        await self._generate_prompt_catalog(output_dir)
        # 5. Event Reference
        await self._generate_event_docs(output_dir)
        # 6. Schema Reference (JSON Schema)
        await self._generate_schema_docs(output_dir)
```

**Saída Gerada**

```
docs/
├── api/
│   └── openapi.json          # Spec OpenAPI completa
├── agents/
│   ├── triage.md             # Docs do agente de triagem
│   ├── vendas.md             # Docs do agente de vendas
│   └── suporte.md
├── skills/
│   ├── web_search.md
│   ├── knowledge_base.md
│   └── calendar.md
├── prompts/
│   ├── vendas.system.md      # Docs do prompt com versões
│   └── suporte.system.md
├── schemas/
│   ├── Message.json
│   ├── AgentConfig.json
│   └── HandoffRequest.json
└── events/
    └── reference.md          # Todos os eventos do sistema
```

## 11.7 SDK de Extensão

Para facilitar a criação de plugins (skills, channels, guardrails), a jClaw fornece um SDK com helpers e decorators.

```python
from jclaw.sdk import skill, tool, guardrail, channel

# Criação simplificada de Skill com decorators
@skill(id="meu_crm", name="CRM Integration", version="1.0.0")
class CRMSkill:

    @tool(
        name="buscar_cliente",
        description="Busca cliente pelo nome ou CPF",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Nome ou CPF"},
            },
            "required": ["query"],
        },
    )
    async def buscar_cliente(self, query: str,
                              ctx: SkillContext) -> ToolResult:
        cliente = await self.crm_api.search(query)
        return ToolResult(output=cliente.to_dict())

    @tool(
        name="criar_oportunidade",
        description="Cria oportunidade de venda no CRM",
    )
    async def criar_oportunidade(self, cliente_id: str,
                                   produto: str,
                                   valor: float,
                                   ctx: SkillContext) -> ToolResult:
        opp = await self.crm_api.create_opportunity(
            cliente_id=cliente_id, produto=produto, valor=valor
        )
        return ToolResult(output={"id": opp.id, "status": "created"})


# Criação simplificada de Guardrail
@guardrail(id="brand_voice", type="output")
async def brand_voice_check(message: Message,
                             context: GuardrailContext) -> GuardrailResult:
    """Valida se a resposta segue o tom de voz da marca."""
    # Lógica de validação
    if contains_informal_language(message.content):
        return GuardrailResult(
            action="warn",
            reason="Resposta contém linguagem informal",
            modified_content=formalize(message.content),
        )
    return GuardrailResult(action="pass")
```

## 11.8 Configuração de Ambiente de Desenvolvimento

```yaml
# docker-compose.dev.yaml
services:
  jclaw:
    build: .
    command: jclaw serve --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"    # API
      - "8001:8001"    # Playground Web
    environment:
      - JCLAW_ENV=development
      - JCLAW_LOG_LEVEL=DEBUG
    depends_on:
      - postgres
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: jclaw_dev
      POSTGRES_PASSWORD: dev

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./observability/dashboards:/var/lib/grafana/dashboards
```

---

# 12. Guardrails, Segurança e Observabilidade

## 12.1 Pipeline de Guardrails

Guardrails são filtros que validam mensagens de entrada e saída. Cada guardrail pode bloquear, modificar ou anotar uma mensagem.

```python
class Guardrail(ABC):
    @abstractmethod
    async def check(
        self, message: Message, context: GuardrailContext
    ) -> GuardrailResult:
        """Retorna PASS, WARN ou BLOCK."""

class GuardrailResult(BaseModel):
    action: Literal["pass", "warn", "block"]
    reason: str | None = None
    modified_content: str | None = None  # Se modificável
    metadata: dict[str, Any] = {}
```

**Guardrails Nativos**

| Guardrail | Tipo | Descrição |
|---|---|---|
| pii_detector | Input + Output | Detecta e mascara CPF, email, telefone, cartão de crédito |
| prompt_injection | Input | Detecta tentativas de injeção de prompt |
| toxicity_filter | Input + Output | Filtra conteúdo tóxico, ofensivo ou NSFW |
| topic_guardrail | Input | Bloqueia tópicos fora do escopo do agente |
| hallucination_check | Output | Valida factos contra a base de conhecimento |
| max_length | Output | Trunca respostas que excedem o limite |
| rate_limiter | Input | Limita requisições por usuário/sessão |

## 12.2 Observabilidade

- **Tracing:** Cada requisição gera um span OpenTelemetry com: `agent_id`, `session_id`, `llm_model`, `latency`, `tokens_in`, `tokens_out`, `tool_calls`, `handoffs`, `prompt_version`.
- **Métricas Prometheus:** `llm_requests_total`, `llm_latency_seconds`, `llm_tokens_total`, `handoff_total`, `guardrail_blocks_total`, `active_sessions_gauge`, `prompt_render_time_seconds`, `prompt_tokens_gauge`.
- **Logs Estruturados:** JSON via structlog; correlation via `trace_id`; níveis configuráveis por módulo.
- **Dashboard:** Template Grafana incluso com painéis de latência, custo estimado, erros, distribuição de agentes e analytics de prompts.

---

# 13. Persistência e Infraestrutura

## 13.1 Modelo de Dados (PostgreSQL)

```sql
-- Tabelas principais
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(50) NOT NULL,
    chat_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    active_agent_id VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL,        -- user | assistant | system | tool
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_results JSONB,
    agent_id VARCHAR(100),
    tokens_used INT,
    model_used VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE memory_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    fact_key VARCHAR(255) NOT NULL,
    fact_value TEXT NOT NULL,
    embedding VECTOR(1536),            -- pgvector
    source_session_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE handoff_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    source_agent_id VARCHAR(100),
    target_agent_id VARCHAR(100),
    mode VARCHAR(20),
    reason TEXT,
    context_payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    engine VARCHAR(20) DEFAULT 'jinja2',
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    tags TEXT[] DEFAULT '{}',
    parent_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(template_id, version)
);

CREATE TABLE prompt_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    agent_id VARCHAR(100),
    session_id UUID,
    tokens_used INT,
    render_time_ms FLOAT,
    layers_used TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 13.2 Redis — Uso

- **Sessões ativas:** Hash com histórico recente, TTL configurável (chave: `session:{id}`).
- **Rate limiting:** Sliding window counter por user_id (chave: `ratelimit:{user_id}`).
- **Locks distribuídos:** Para evitar processamento duplo de webhooks (chave: `lock:msg:{message_id}`).
- **Circuit breaker state:** Estado de cada provider (chave: `cb:{provider_id}`).
- **Prompt cache:** Cache de prompts renderizados (chave: `prompt_cache:{agent_id}:{version}`).

---

# 14. Configuração e Variáveis de Ambiente

## 14.1 Variáveis de Ambiente (.env)

```bash
# ─── Core ───
JCLAW_ENV=production                        # development | staging | production
JCLAW_LOG_LEVEL=INFO
JCLAW_SECRET_KEY=<random-256-bit-key>

# ─── Database ───
JCLAW_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/jclaw
JCLAW_REDIS_URL=redis://localhost:6379/0

# ─── LLM Providers ───
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk_...

# ─── Canais ───
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_WEBHOOK_URL=https://api.meusite.com/webhooks/telegram
TELEGRAM_WEBHOOK_SECRET=meu-secret

WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_ACCESS_TOKEN=EAAx...
WHATSAPP_VERIFY_TOKEN=meu-verify-token
WHATSAPP_WEBHOOK_URL=https://api.meusite.com/webhooks/whatsapp

# ─── Observabilidade ───
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=jclaw
```

## 14.2 agents.yaml — Definição Declarativa

```yaml
agents:
  - agent_id: triage
    name: "Agente de Triagem"
    description: "Identifica a intenção e roteia para o especialista"
    system_prompt: |
      Você é o agente de triagem da empresa X.
      Identifique a intenção do usuário e transfira
      para o agente especializado.
    llm_provider: anthropic
    llm_model: claude-haiku-4-5-20251001
    temperature: 0.3
    max_tokens: 1024
    context_window: 32000
    skills: [handoff_to_agent]
    handoff_targets: [vendas, suporte, financeiro]
    memory:
      strategy: sliding_window
      max_messages: 20

  - agent_id: vendas
    name: "Agente de Vendas"
    system_prompt: "prompts/vendas/system.j2"  # Referência ao template
    llm_provider: anthropic
    llm_model: claude-sonnet-4-20250514
    temperature: 0.7
    max_tokens: 4096
    context_window: 128000
    skills: [knowledge_base, calendar, handoff_to_agent]
    handoff_targets: [triage, suporte]
    memory:
      strategy: hybrid
      max_tokens: 8000
      persist_to_long_term: true
    prompt_config:
      version: "2.1.0"
      layers: !include prompts/vendas/layers.yaml
      pipeline: [StripWhitespace, InjectMemoryFacts, TokenBudgetEnforcer]
```

---

# 15. Interfaces e Contratos (Schemas)

Todos os contratos da plataforma são definidos via Pydantic v2 e exportam JSON Schema automaticamente para documentação e validação.

## 15.1 Modelos de Mensagem

```python
class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = {}

class ToolCall(BaseModel):
    id: str
    name: str
    input: dict[str, Any]

class ToolResult(BaseModel):
    tool_call_id: str
    output: str | dict[str, Any]
    is_error: bool = False
```

## 15.2 Modelos de Resposta LLM

```python
class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] = []
    stop_reason: Literal["end_turn", "tool_use",
                          "max_tokens", "stop_sequence"]
    model: str
    usage: TokenUsage
    latency_ms: float

class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float | None = None

class StreamChunk(BaseModel):
    delta: str
    chunk_type: Literal["text", "tool_call", "stop"]
    tool_call: ToolCall | None = None
```

## 15.3 Eventos do Sistema

```python
class JClawEvent(BaseModel):
    event_type: str
    timestamp: datetime
    session_id: str | None = None
    agent_id: str | None = None
    trace_id: str | None = None
    payload: dict[str, Any] = {}

# Eventos emitidos:
# message.received, message.sent
# llm.request, llm.response, llm.error
# handoff.requested, handoff.completed, handoff.failed
# skill.executed, skill.error
# guardrail.triggered, guardrail.blocked
# session.created, session.expired
# memory.compacted, memory.fact_extracted
# prompt.rendered, prompt.version_changed, prompt.test_passed, prompt.test_failed
```

---

# 16. Roadmap e Extensões Futuras

| Fase | Funcionalidade | Descrição |
|---|---|---|
| v1.0 (MVP) | Core + Telegram + Anthropic | Orquestrador, memória, handoffs, 1 canal, 1 provider |
| v1.1 | WhatsApp + Multi-LLM | Canal WhatsApp, OpenAI e Groq como providers adicionais |
| v1.2 | Skills System + RAG | Registry de skills, knowledge_base com pgvector |
| v1.3 | Guardrails + Observability | Pipeline de guardrails, OpenTelemetry, dashboard Grafana |
| v1.4 | Prompt Systems + CLI | Engine de prompts, versionamento, CLI com playground |
| v1.5 | Developer Systems | Hot-reload, scaffold, inspector, docs auto-geradas |
| v2.0 | Voice + Multimodal | Canais de voz (Twilio), processamento de imagens no pipeline |
| v2.1 | Studio Visual | UI drag-and-drop para compor fluxos de agentes e handoffs |
| v2.2 | Prompt A/B Testing | Testes A/B de prompts em produção com split de tráfego |
| v2.3 | Multi-tenant | Isolamento de dados por tenant, billing integrado |
| v3.0 | Agent Marketplace | Marketplace de skills, prompts e agentes pré-construídos |

---

**jClaw** — Especificação Técnica v2.0.0 — Abril 2026

*Documento gerado como referência para desenvolvimento. Sujeito a revisões.*
