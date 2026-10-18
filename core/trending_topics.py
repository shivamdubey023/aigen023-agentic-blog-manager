"""Curated and dynamic trending tech topics for organic SEO and high AdSense CPC."""
from __future__ import annotations
import random
from typing import Any

CURATED_TRENDING_TOPICS = [
    {
        "topic": "Python 3.13 Free-Threaded Mode (No-GIL): Benchmark and Migration Guide",
        "keyword": "python 3.13 no gil free threaded",
        "category": "Python & Backend",
        "cpc_tier": "High",
        "audience": "Working developer",
    },
    {
        "topic": "Deploying DeepSeek R1 Locally with Ollama and FastAPI: Full Production Setup",
        "keyword": "deepseek r1 ollama fastapi deployment",
        "category": "AI & LLMs",
        "cpc_tier": "Very High",
        "audience": "Working developer",
    },
    {
        "topic": "FastAPI vs Go Gin in 2026: Real Latency Benchmarks under High Concurrency",
        "keyword": "fastapi vs go gin benchmark",
        "category": "Backend Engineering",
        "cpc_tier": "High",
        "audience": "Working developer",
    },
    {
        "topic": "Fixing Django PostgreSQL Connection Pooling: PgBouncer vs Database Engine Pools",
        "keyword": "django pgbouncer connection pooling",
        "category": "Databases & Python",
        "cpc_tier": "High",
        "audience": "Working developer",
    },
    {
        "topic": "Docker Multi-Stage Builds for Python Apps: Slashing Image Size from 1.2GB to 90MB",
        "keyword": "docker multi stage build python slim image",
        "category": "DevOps & Containers",
        "cpc_tier": "High",
        "audience": "Working developer",
    },
    {
        "topic": "Building an Autonomous AI Agent with LangGraph and SQLite State Persistence",
        "keyword": "langgraph sqlite persistence tutorial",
        "category": "AI Engineering",
        "cpc_tier": "Very High",
        "audience": "Working developer",
    },
    {
        "topic": "Asyncio TaskGroup in Python: Replacing asyncio.gather with Safer Concurrency",
        "keyword": "python asyncio taskgroup exception handling",
        "category": "Python Architecture",
        "cpc_tier": "High",
        "audience": "Working developer",
    },
    {
        "topic": "Securing REST APIs with OAuth2 and PKCE: Complete Implementation from Scratch",
        "keyword": "oauth2 pkce fastapi implementation",
        "category": "Cybersecurity & APIs",
        "cpc_tier": "Very High",
        "audience": "Senior engineer",
    },
    {
        "topic": "Redis Caching Strategies for High-Traffic Web APIs: Cache-Aside vs Write-Through",
        "keyword": "redis cache aside pattern python",
        "category": "System Design",
        "cpc_tier": "Very High",
        "audience": "Working developer",
    },
    {
        "topic": "Top 15 Python Interview Questions for Senior Backend Engineers in 2026",
        "keyword": "python senior developer interview questions 2026",
        "category": "Career & Interviews",
        "cpc_tier": "High",
        "audience": "Working developer",
    },
]

def get_random_trending_topic() -> dict[str, Any]:
    """Pick a trending, high-intent topic to generate a blog post without manual brainstorming."""
    return random.choice(CURATED_TRENDING_TOPICS)

def list_all_trending_topics() -> list[dict[str, Any]]:
    return CURATED_TRENDING_TOPICS
