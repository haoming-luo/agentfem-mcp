FROM python:3.12-slim-bookworm

ARG AGENTFEM_MCP_VERSION=0.1.0

LABEL org.opencontainers.image.title="AgentFEM MCP" \
      org.opencontainers.image.description="Official MCP interface for the AgentFEM finite-element platform" \
      org.opencontainers.image.source="https://github.com/haoming-luo/agentfem-mcp" \
      org.opencontainers.image.licenses="Apache-2.0"

RUN python -m pip install --no-cache-dir \
      "agentfem-mcp==${AGENTFEM_MCP_VERSION}" \
    && useradd --create-home --uid 10001 agentfem

WORKDIR /workspace
ENV AGENTFEM_MCP_ROOTS=/workspace \
    PYTHONUNBUFFERED=1

USER agentfem

ENTRYPOINT ["agentfem-mcp"]
