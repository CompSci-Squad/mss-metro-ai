# Arquitetura e Injeção de Dependências

## 🏗️ Visão Geral

Este projeto foi refatorado para seguir princípios de **Engenharia de Software** modernos:

- **Injeção de Dependências (DI)** usando `dependency-injector`
- **SOLID Principles** (Single Responsibility, Dependency Inversion)
- **Orientação a Objetos** com classes bem encapsuladas
- **Separation of Concerns** (separação de responsabilidades)
- **Interface Segregation** usando Protocols

## 📦 Estrutura do Projeto

```
app/
├── core/
│   ├── interfaces.py      # Protocolos e interfaces abstratas
│   ├── container.py        # Container de injeção de dependências
│   ├── settings.py         # Configurações centralizadas
│   └── logger.py           # Logger estruturado
├── clients/
│   ├── cache_client.py     # Cliente Redis (implementa CacheClientInterface)
│   ├── opensearch_client.py # Cliente OpenSearch (implementa VectorStoreInterface)
│   └── s3_client.py        # Cliente S3
├── services/
│   ├── vlm_service.py      # Serviço VLM (implementa VLMServiceInterface)
│   ├── embedding_service.py # Serviço de embeddings (implementa EmbeddingServiceInterface)
│   └── langchain_service.py # Serviço LangChain (implementa QueryServiceInterface)
├── routes/
│   ├── uploads.py          # Rotas de upload (usa DI)
│   ├── queries.py          # Rotas de consulta (usa DI)
│   └── health.py           # Health check
├── schemas/
│   ├── upload.py           # Schemas Pydantic para uploads
│   └── query.py            # Schemas Pydantic para queries
└── workers/
    └── image_processing.py # Workers Celery (usa DI)
```

## 🔌 Injeção de Dependências

### Como Funciona

1. **Container Centralizado** (`core/container.py`):
   - Define todos os providers (Singleton, Factory, etc.)
   - Gerencia ciclo de vida dos objetos
   - Conecta dependências automaticamente

2. **Interfaces** (`core/interfaces.py`):
   - Define contratos usando `Protocol` e `ABC`
   - Permite trocar implementações facilmente
   - Facilita testes com mocks

3. **Wiring Automático**:
   - Container injeta dependências nas rotas
   - Usa decorators do FastAPI `Depends()`
   - Reduz acoplamento entre componentes

### Exemplo de Uso nas Rotas

**Antes (sem DI):**
```python
@router.post("/upload")
async def upload_file(project_id: str, file: UploadFile):
    opensearch = get_opensearch_client()  # Singleton global
    cache = get_cache_client()            # Singleton global
    # ... código acoplado
```

**Depois (com DI):**
```python
from dependency_injector.wiring import inject, Provide
from app.core.container import Container

@router.post("/upload")
@inject
async def upload_file(
    project_id: str,
    file: UploadFile,
    opensearch: OpenSearchClient = Depends(Provide[Container.opensearch_client]),
    cache: RedisCache = Depends(Provide[Container.cache_client]),
):
    # Dependências injetadas automaticamente
    # Fácil de testar com mocks
```

## 🎯 Princípios SOLID Aplicados

### Single Responsibility Principle (SRP)
Cada classe tem uma única responsabilidade:
- `RedisCache` → apenas cache
- `OpenSearchClient` → apenas vector store
- `VLMService` → apenas processamento VLM
- `EmbeddingService` → apenas embeddings

### Open/Closed Principle (OCP)
Classes abertas para extensão, fechadas para modificação:
- Interfaces permitem novas implementações
- Container permite trocar providers

### Liskov Substitution Principle (LSP)
Implementações podem ser substituídas pelas interfaces:
- `RedisCache` implementa `CacheClientInterface`
- Pode ser substituído por `MemcachedCache` sem quebrar código

### Interface Segregation Principle (ISP)
Interfaces específicas para cada cliente:
- `CacheClientInterface` → métodos de cache
- `VectorStoreInterface` → métodos de vector store
- Não força implementação de métodos desnecessários

### Dependency Inversion Principle (DIP)
Depende de abstrações, não de implementações concretas:
- Rotas dependem de interfaces
- Container injeta implementações concretas
- Fácil trocar Redis por outro cache

## 🔧 Benefícios da Refatoração

### 1. Testabilidade
```python
# Testes são fáceis com DI
def test_upload_route():
    mock_opensearch = Mock(spec=OpenSearchClient)
    mock_cache = Mock(spec=RedisCache)
    
    # Injetar mocks nas rotas
    # Testar comportamento isolado
```

### 2. Manutenibilidade
- Código mais limpo e organizado
- Responsabilidades bem definidas
- Fácil localizar e corrigir bugs

### 3. Escalabilidade
- Adicionar novos serviços é simples
- Trocar implementações sem quebrar código
- Container gerencia complexidade

### 4. Reusabilidade
- Classes independentes podem ser reutilizadas
- Interfaces permitem múltiplas implementações
- Reduz duplicação de código

## 📝 Como Adicionar Novo Serviço

### 1. Criar Interface
```python
# core/interfaces.py
class NewServiceInterface(ABC):
    @abstractmethod
    async def do_something(self, data: str) -> str:
        pass
```

### 2. Criar Implementação
```python
# services/new_service.py
class NewService(NewServiceInterface):
    def __init__(self, config: str):
        self.config = config
    
    async def do_something(self, data: str) -> str:
        return f"Processed: {data}"
```

### 3. Adicionar ao Container
```python
# core/container.py
class Container(containers.DeclarativeContainer):
    # ...
    new_service = providers.Singleton(
        NewService,
        config="my-config"
    )
```

### 4. Usar nas Rotas
```python
# routes/my_route.py
@router.post("/process")
@inject
async def process(
    data: str,
    service: NewService = Depends(Provide[Container.new_service]),
):
    result = await service.do_something(data)
    return {"result": result}
```

## 🧪 Testes com DI

```python
import pytest
from unittest.mock import Mock
from dependency_injector import containers, providers

# Criar container de teste
class TestContainer(containers.DeclarativeContainer):
    cache_client = providers.Singleton(Mock)
    opensearch_client = providers.Singleton(Mock)

# Usar em testes
def test_my_route():
    container = TestContainer()
    # ... configurar mocks
    # ... testar rota
```

## 🚀 Próximos Passos

1. ✅ Interfaces e Container criados
2. ✅ Clientes refatorados com DI
3. 🔄 Rotas sendo refatoradas para usar @inject
4. ⏳ Workers Celery para usar DI
5. ⏳ Testes unitários com mocks
6. ⏳ Documentação completa

## 📚 Referências

- [dependency-injector docs](https://python-dependency-injector.ets-labs.org/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
