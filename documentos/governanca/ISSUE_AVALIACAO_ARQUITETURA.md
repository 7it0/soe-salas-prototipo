# Avaliação da arquitetura institucional do piloto SOE

## Contexto

O piloto das páginas técnicas das Salas de Acompanhamento e de Crise já demonstra que é possível reunir, por reunião, síntese executiva, análises por instituição, gráficos e mapas, cruzamento técnico, Nota Técnica integral e anexo estruturado em um ambiente versionável e de consulta rápida.

A discussão agora proposta é sobre a **evolução institucional do piloto**, e não sobre a adoção automática de uma tecnologia específica.

A minuta de Nota Técnica disponível em `documentos/governanca/` procura transformar o piloto em um caso de uso concreto para debate com a STI e demais áreas envolvidas.

## Perguntas para avaliação

1. **Hospedagem e custódia** — Qual ambiente institucional deveria hospedar páginas, código, documentos e arquivos derivados? O GitHub institucional pode cumprir parte desse papel?
2. **Persistência** — Como garantir URLs estáveis, versionamento, histórico e preservação digital?
3. **Metadados** — Quais campos devem ser obrigatórios para permitir busca, catálogo, BI, Conjuntura e reaproveitamento anual?
4. **Acesso** — Como separar:
   - conteúdo público;
   - conteúdo destinado a órgãos estaduais/regionais autenticados;
   - conteúdo interno ou operacional restrito?
5. **Identidade e autenticação** — Há infraestrutura existente na ANA que possa ser usada para SSO/OIDC/OAuth2 e controle de perfis?
6. **Interoperabilidade** — Quais APIs, bancos, catálogos ou serviços geoespaciais existentes podem ser reutilizados?
7. **Geodados** — Há capacidade institucional para oferecer, quando aplicável, PostGIS, GeoServer/OGC API, WMS/WFS/WCS, COG e APIs REST de séries temporais?
8. **Segurança e auditoria** — Quais requisitos de logs, rate limiting, revisão, gestão de permissões e segregação de ambientes devem ser adotados?
9. **Piloto institucional** — Qual seria o menor escopo viável para testar a arquitetura com baixo risco e sem interromper a rotina das Salas?
10. **Integração com Estados** — Como esse desenho poderia, em etapa posterior, apoiar uma arquitetura federada de dados com órgãos estaduais, iniciando por um piloto no Nordeste?

## Resultado esperado desta Issue

Registrar contribuições e identificar:

- capacidades já existentes;
- lacunas técnicas;
- decisões de governança necessárias;
- responsáveis por cada domínio;
- condições para um piloto institucional;
- itens que exigem manifestação da ASCOM, STI, SOE ou outras unidades.

> **Status:** discussão preliminar. Este registro não representa decisão institucional da ANA.