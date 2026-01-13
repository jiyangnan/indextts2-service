# IndexTTS2 微服务 Makefile

.PHONY: help install dev test build docker-push deploy

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

## help: 显示帮助信息
help:
	@echo "$(BLUE)IndexTTS2 微服务 - 可用命令$(NC)"
	@echo ""
	@echo "$(GREEN)开发命令:$(NC)"
	@sed -n '/^## /p' $(MAKEFILE_LIST) | sed 's/## /  /' | column -t -s ':'
	@echo ""
	@echo "$(GREEN)部署命令:$(NC)"
	@sed -n '/^### /p' $(MAKEFILE_LIST) | sed 's/### /  /' | column -t -s ':'

## install: 安装依赖
install:
	@echo "$(BLUE)安装依赖...$(NC)"
	@pip install uv
	@uv sync --all-extras

## dev: 启动开发服务器
dev:
	@echo "$(BLUE)启动开发服务器...$(NC)"
	@uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## test: 运行测试
test:
	@echo "$(BLUE)运行测试...$(NC)"
	@uv run pytest

## lint: 代码检查
lint:
	@echo "$(BLUE)代码检查...$(NC)"
	@uv run ruff check app/
	@uv run mypy app/

## format: 代码格式化
format:
	@echo "$(BLUE)格式化代码...$(NC)"
	@uv run black app/
	@uv run ruff check --fix app/

## build: 构建 Docker 镜像
build:
	@echo "$(BLUE)构建 Docker 镜像...$(NC)"
	@docker build -t indextts2-service:latest .

### docker-push: 推送 Docker 镜像
docker-push: build
	@echo "$(BLUE)推送镜像...$(NC)"
	@docker push indextts2-service:latest

### deploy: 部署到 RunPod
deploy:
	@echo "$(BLUE)部署到 RunPod...$(NC)"
	@chmod +x scripts/deploy-runpod.sh
	@./scripts/deploy-runpod.sh

### stop: 停止 RunPod 实例
stop:
	@echo "$(BLUE)停止 RunPod 实例...$(NC)"
	@chmod +x scripts/stop-runpod.sh
	@./scripts/stop-runpod.sh

## clean: 清理临时文件
clean:
	@echo "$(BLUE)清理临时文件...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache
	@rm -rf dist
	@rm -rf *.egg-info
