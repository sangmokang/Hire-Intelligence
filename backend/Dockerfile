# ── builder stage: 의존성 설치 ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── runtime stage: 최소 이미지 ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# builder에서 설치된 패키지만 복사 (dev 도구 제외)
COPY --from=builder /install /usr/local

# 애플리케이션 소스 복사
COPY . .

# non-root 사용자로 실행 (컨테이너 보안)
RUN useradd -r -u 1001 -s /bin/false appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# alembic upgrade head는 fly.toml release_command에서 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
