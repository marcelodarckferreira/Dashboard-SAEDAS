# Especificação de Cache com Redis

Esta especificação define os padrões e regras para o uso do Redis como camada de cache e persistência de estado no ecossistema SAEDAS.

## 1. Objetivos Técnicos
- **Performance:** Reduzir o tempo de carregamento das telas de segundos para milissegundos.
- **Eficiência:** Evitar o re-processamento de CSVs pesados e agregações complexas do Pandas.
- **Persistência:** Manter o estado da sessão e filtros do usuário entre restarts do container.

## 2. Configuração de Conexão
As credenciais devem ser lidas exclusivamente das variáveis de ambiente:
- `REDIS_HOST`: Padrão `redis` no Docker ou `localhost` localmente.
- `REDIS_PORT`: Padrão `6379`.
- `REDIS_PASSWORD`: Definida no `.env`.
- `REDIS_DB`: Padrão `0`.

## 3. Padrão de Nomenclatura de Chaves (Keys)
Para garantir a organização e evitar colisões, as chaves devem seguir o formato:
`saedas:{escopo}:{tipo}:{identificador}`

**Exemplos:**
- `saedas:home:dataset:main` -> DataFrame principal da Home.
- `saedas:session:{session_id}:filters` -> Filtros ativos de uma sessão.
- `saedas:cache:kpi:vacinacao_total` -> Valor agregado de um KPI específico.

## 4. Estratégia de Serialização
Como o Redis armazena strings/bytes, utilizaremos:
- **DataFrames:** Serialização via `pickle` (compressão opcional) ou `pyarrow`.
- **Dicionários/Objetos Simples:** Serialização via `json`.

## 5. Política de Invalidação (Smart Cache)
O SAEDAS utiliza um mecanismo de **Invalidação por Timestamp** para garantir paridade entre o disco e a RAM:
- **Timestamp Validation:** Antes de carregar do Redis, o sistema verifica a data de modificação (`mtime`) do arquivo CSV original.
- **Auto-Invalidation:** Se o arquivo no disco for mais novo que o registro no cache, o cache é automaticamente invalidado e o arquivo é re-lido e re-cacheado.
- **TTL (Time To Live):** Por padrão, os registros expiram em **12 horas**, mesmo que o arquivo não mude.

## 6. Implementação (utils/redis_client.py)
Deve ser implementada uma classe `RedisClient` seguindo o padrão Singleton para gerenciar a conexão e fornecer métodos auxiliares:
- `set_dataframe(key, df, ttl)`
- `get_dataframe(key)`
- `set_object(key, obj, ttl)`
- `get_object(key)`

## 7. Referências nas Telas
Cada tela que implementar Redis deve linkar esta spec e definir suas chaves específicas no seu respectivo arquivo de spec.
