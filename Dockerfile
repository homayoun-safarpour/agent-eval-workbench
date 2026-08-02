FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples
RUN pip install --no-cache-dir -e .
RUN useradd --create-home --uid 10001 workbench
USER workbench
ENTRYPOINT ["agent-eval"]
CMD ["run", "examples/scenarios/benchmark.yaml", "--output", "/tmp/benchmark.json"]
