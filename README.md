# Jira Tools MCP

Este projeto fornece uma integração entre o Jira e assistentes de IA através do Model Context Protocol (MCP). Ele permite que assistentes como o Claude possam interagir diretamente com o Jira para criar, consultar e gerenciar issues.

## Estrutura do Projeto

```
jira-tools/
├── src/                      # Código fonte principal
│   ├── core/                # Core da aplicação
│   │   └── jira/           # Módulo de integração com Jira
│   │       ├── __init__.py
│   │       └── jira_integration.py  # Implementação base das operações Jira
│   ├── mcp/                 # Módulo do servidor MCP
│   │   ├── __init__.py
│   │   └── server.py       # Implementação do servidor MCP
│   └── tools/              # Ferramentas e utilitários
│       └── langchain/      # Ferramentas LangChain
│           └── jira_tools.py  # Implementação das ferramentas LangChain
├── config.py               # Configurações globais
├── main.py                # Ponto de entrada da aplicação
├── pyproject.toml         # Configuração do projeto Python
├── README.md             # Documentação do projeto
└── .env                  # Variáveis de ambiente (não versionado)
```

### Descrição dos Módulos

#### 1. Core (`src/core/`)
- **jira_integration.py**: Implementa a integração base com a API do Jira
  - Gerenciamento de cliente Jira
  - Operações CRUD de issues
  - Gerenciamento de transições
  - Consulta de tipos de issues
  - Tratamento de campos customizados

#### 2. MCP Server (`src/mcp/`)
- **server.py**: Implementa o servidor MCP
  - Expõe as funcionalidades do Jira via MCP
  - Gerencia o protocolo de comunicação
  - Processa requisições do Claude Desktop
  - Formata respostas conforme especificação MCP

#### 3. LangChain Tools (`src/tools/langchain/`)
- **jira_tools.py**: Implementa ferramentas LangChain
  - Define ferramentas reutilizáveis
  - Integra com outros agentes LangChain
  - Fornece interfaces padronizadas

#### 4. Configuração
- **config.py**: Configurações globais do projeto
- **pyproject.toml**: Dependências e metadados
- **.env**: Credenciais e configurações sensíveis

## Funcionalidades

- Criar issues no Jira
- Consultar detalhes de issues
- Gerenciar transições de status
- Listar tipos de issues disponíveis
- Suporte completo para campos customizados
- Integração com Claude Desktop via MCP

## Requisitos

- Python 3.12+
- Conta no Jira com token de API
- Claude Desktop (para integração MCP)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/jira-tools.git
cd jira-tools
```

2. Instale as dependências:
```bash
uv sync
```

3. Configure as variáveis de ambiente criando um arquivo `.env`:
```env
JIRA_URL=https://sua-instancia.atlassian.net
JIRA_ACCOUNT_EMAIL=seu-email@exemplo.com
JIRA_API_TOKEN=seu-token-api
```


4. Adicione a configuração do servidor MCP:
```json
{
  "mcpServers": {
    "jira-tools": {
      "command": "uv",
      "args": [
        "--directory",
        "/caminho/absoluto/para/jira-tools",
        "run",
        "src/mcp/server.py"
      ]
    }
  }
}
```

Substitua `/caminho/absoluto/para/jira-tools` pelo caminho completo onde você clonou o repositório.

## Ferramentas Disponíveis

O servidor MCP expõe as seguintes ferramentas para o Claude:

### 1. Criar Issue
```python
create_jira_issue(
    project: str,
    title: str,
    issue_type: str,
    description: str,
    parent: str = None,
    assignee_email: str = None,
    custom_fields: Dict = None
)
```

### 2. Consultar Detalhes da Issue
```python
get_issue_info(issue_key: str) -> Dict[str, str]
```

### 3. Obter Transições Disponíveis
```python
get_transitions(issue_key: str) -> Dict[str, str]
```

### 4. Executar Transição
```python
transition_issue(issue_key: str, transition_name: str) -> str
```

### 5. Listar Tipos de Issues
```python
get_issue_types() -> Dict[str, Dict[str, str]]
```

## Usando com Claude Desktop

### Configuração Inicial

1. Inicie o Claude Desktop
2. Procure pelo ícone de ferramentas na interface (ícone de chave inglesa)
3. Você verá as ferramentas do Jira disponíveis no painel lateral

### Operações Disponíveis

O Claude pode realizar várias operações no Jira. Aqui estão algumas sugestões de como pedir:

#### Gerenciamento de Issues
- "Crie uma nova tarefa no projeto X"
- "Adicione uma subtarefa à PROJ-123"
- "Mostre os detalhes da issue PROJ-456"

#### Transições de Status
- "Quais transições estão disponíveis para PROJ-789?"
- "Mova a issue PROJ-123 para 'Em Desenvolvimento'"
- "Conclua a tarefa PROJ-456"

#### Consultas e Relatórios
- "Liste todos os tipos de issues disponíveis"
- "Qual o status atual da PROJ-123?"
- "Mostre a descrição da issue PROJ-456"

#### Campos Customizados
- "Crie uma issue com o campo customizado X igual a Y"
- "Adicione uma issue ao épico PROJ-789"
- "Crie uma tarefa na squad de Backend"

## Exemplos de Uso com Claude

Aqui estão alguns exemplos de como interagir com o Jira através do Claude:

1. Criar uma nova issue:
```
"Crie uma issue do tipo 'Tarefa' no projeto PROJ com o título 'Implementar novo recurso'"
```

2. Consultar uma issue:
```
"Quais são os detalhes da issue PROJ-123?"
```

3. Mudar status:
```
"Mude o status da issue PROJ-123 para 'Em Andamento'"
```

4. Ver tipos disponíveis:
```
"Quais são os tipos de issues disponíveis no Jira?"
```



### Adicionando Novas Funcionalidades

1. Integração com Jira:
   - Adicione novos métodos em `src/core/jira/jira_integration.py`
   - Use o decorador `@with_jira_client`
   - Documente parâmetros e retornos

2. Ferramentas MCP:
   - Adicione novas ferramentas em `src/mcp/server.py`
   - Use o decorador `@mcp.tool()`
   - Forneça documentação clara para o Claude

3. Testes:
   - Adicione testes unitários em `tests/`
   - Crie mocks para chamadas Jira
   - Teste cenários de erro

### Guidelines de Código

1. Estilo:
   - Siga PEP 8
   - Use type hints
   - Documente com docstrings

2. Commits:
   - Use mensagens descritivas
   - Um commit por funcionalidade
   - Referencie issues relacionadas

3. Pull Requests:
   - Descreva as mudanças
   - Inclua testes
   - Atualize a documentação

## Troubleshooting

### Problemas Comuns e Soluções

#### 1. Erro de Conexão com o Jira
```
Problema: "Unable to connect to Jira server"
Solução: 
- Verifique se JIRA_URL está correta no .env
- Confirme se o servidor Jira está acessível
- Verifique sua conexão com a internet
```

#### 2. Erro de Autenticação
```
Problema: "Authentication failed"
Solução:
- Verifique JIRA_ACCOUNT_EMAIL no .env
- Confirme se JIRA_API_TOKEN está correto
- Gere um novo token de API se necessário
```

#### 3. MCP não aparece no Claude
```
Problema: Ferramentas não aparecem no Claude Desktop
Solução:
- Verifique o caminho em claude_desktop_config.json
- Confirme se está usando caminhos absolutos
- Reinicie o Claude Desktop
```

#### 4. Erros de Permissão
```
Problema: "User is not authorized"
Solução:
- Verifique as permissões do token no Jira
- Confirme se tem acesso aos projetos
- Solicite permissões necessárias se preciso
```

### Logs e Diagnóstico

1. Logs do MCP Server:
```bash
tail -f ~/.local/state/claude/logs/mcp-servers.log
```

2. Verificar Configuração:
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

3. Testar Conexão Jira:
```bash
python -c "from src.core.jira.jira_integration import init_jira_client; init_jira_client()"
```

## Licença

GPLv3 - https://www.gnu.org/licenses/gpl-3.0.html