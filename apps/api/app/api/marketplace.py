"""Marketplace API — discover, install, update, and manage agents,
workflows, tools, and provider plugins from the built-in catalog."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.plugin_registry import get_plugin_registry
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.models.marketplace import (
    InstalledMarketplaceItem,
    InstallStatus,
    MarketplaceItemType,
)
from app.models.plugin import PluginManifest, PluginPermission, PluginType
from app.schemas.marketplace import (
    InstalledItemResponse,
    InstallRequest,
    InstallResponse,
    MarketplaceItemResponse,
    MarketplaceListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# ── Built-in Catalog ─────────────────────────────────────────────────

BUILTIN_ITEMS = [
    # ── Agents ──
    {"id": "agent-export", "name": "Export Agent", "item_type": "agent", "version": "1.0.0",
     "description": "Specialized agent for export trade operations, buyer discovery, and international market intelligence.",
     "author": "OpenPaper AI", "tags": ["export", "trade", "international", "b2b"],
     "downloads": 1280, "rating": 4.8, "permissions": ["memory:read", "memory:write", "agent:execute", "bus:publish", "bus:subscribe"],
     "dependencies": [], "config_schema": {"type": "object", "properties": {"target_markets": {"type": "array", "items": {"type": "string"}}}},
     "readme": "# Export Agent\\n\\nAutomate export trade workflows, discover international buyers, and generate market intelligence reports."},
    {"id": "agent-sales", "name": "Sales Agent", "item_type": "agent", "version": "1.1.0",
     "description": "AI-powered sales agent for lead qualification, proposal generation, and pipeline management.",
     "author": "OpenPaper AI", "tags": ["sales", "leads", "crm", "pipeline"],
     "downloads": 2450, "rating": 4.9, "permissions": ["memory:read", "memory:write", "agent:execute", "task:read", "task:write"],
     "dependencies": [], "config_schema": {"type": "object", "properties": {"daily_target": {"type": "integer"}}},
     "readme": "# Sales Agent\\n\\nQualify leads, generate proposals, and manage your sales pipeline with AI."},
    {"id": "agent-research", "name": "Research Agent", "item_type": "agent", "version": "1.0.0",
     "description": "Market research specialist for TAM/SAM/SOM analysis, competitive intelligence, and trend forecasting.",
     "author": "OpenPaper AI", "tags": ["research", "market", "competitive", "analysis"],
     "downloads": 3100, "rating": 4.7, "permissions": ["memory:read", "memory:write", "agent:execute", "bus:publish"],
     "dependencies": [], "config_schema": {},
     "readme": "# Research Agent\\n\\nConduct deep market research, competitive analysis, and generate strategic insights."},
    {"id": "agent-seo", "name": "SEO Agent", "item_type": "agent", "version": "1.0.0",
     "description": "SEO optimization specialist for keyword research, content analysis, and search performance tracking.",
     "author": "OpenPaper AI", "tags": ["seo", "marketing", "content", "keywords"],
     "downloads": 890, "rating": 4.5, "permissions": ["memory:read", "memory:write", "agent:execute"],
     "dependencies": [], "config_schema": {},
     "readme": "# SEO Agent\\n\\nOptimize content for search engines with keyword research and performance analysis."},
    {"id": "agent-linkedin", "name": "LinkedIn Agent", "item_type": "agent", "version": "1.0.0",
     "description": "LinkedIn profile optimization, lead generation, and network growth automation agent.",
     "author": "OpenPaper AI", "tags": ["linkedin", "social", "networking", "leads"],
     "downloads": 1560, "rating": 4.6, "permissions": ["memory:read", "memory:write", "agent:execute", "network"],
     "dependencies": [], "config_schema": {},
     "readme": "# LinkedIn Agent\\n\\nAutomate LinkedIn lead generation, profile optimization, and network growth."},
    {"id": "agent-email", "name": "Email Outreach Agent", "item_type": "agent", "version": "1.0.0",
     "description": "Automated email outreach and follow-up campaign manager with template personalization.",
     "author": "OpenPaper AI", "tags": ["email", "outreach", "campaign", "marketing"],
     "downloads": 2100, "rating": 4.4, "permissions": ["memory:read", "memory:write", "agent:execute", "task:read", "task:write"],
     "dependencies": [], "config_schema": {},
     "readme": "# Email Outreach Agent\\n\\nCreate and manage email outreach campaigns with AI-powered personalization."},
    {"id": "agent-support", "name": "Customer Support Agent", "item_type": "agent", "version": "1.0.0",
     "description": "AI customer support agent for ticket triage, response generation, and escalation management.",
     "author": "OpenPaper AI", "tags": ["support", "customer", "ticket", "service"],
     "downloads": 1780, "rating": 4.7, "permissions": ["memory:read", "memory:write", "agent:execute", "task:read", "task:write", "bus:subscribe"],
     "dependencies": [], "config_schema": {},
     "readme": "# Customer Support Agent\\n\\nHandle customer inquiries, triage tickets, and generate AI-powered responses."},

    # ── Workflows ──
    {"id": "wf-lead-gen", "name": "Lead Generation Workflow", "item_type": "workflow", "version": "1.0.0",
     "description": "End-to-end lead generation pipeline: Research → Buyer Finder → Sales Outreach → CRM Update.",
     "author": "OpenPaper AI", "tags": ["leads", "pipeline", "sales", "automation"],
     "downloads": 980, "rating": 4.8, "permissions": ["memory:read", "memory:write", "agent:execute", "bus:publish"],
     "dependencies": ["agent-research", "agent-sales"], "config_schema": {},
     "readme": "# Lead Generation Workflow\\n\\nAutomated pipeline from market research through buyer discovery to sales outreach."},
    {"id": "wf-buyer-discovery", "name": "Export Buyer Discovery Workflow", "item_type": "workflow", "version": "1.0.0",
     "description": "International buyer discovery workflow: Market Analysis → Buyer Finder → Qualification → Outreach.",
     "author": "OpenPaper AI", "tags": ["export", "buyer", "discovery", "international"],
     "downloads": 760, "rating": 4.9, "permissions": ["memory:read", "memory:write", "agent:execute", "bus:publish", "bus:subscribe"],
     "dependencies": ["agent-export", "agent-research"], "config_schema": {},
     "readme": "# Export Buyer Discovery Workflow\\n\\nDiscover and qualify international buyers with automated research and outreach."},
    {"id": "wf-sales-outreach", "name": "Sales Outreach Workflow", "item_type": "workflow", "version": "1.0.0",
     "description": "Multi-channel sales outreach: Lead Qualification → Email Campaign → Follow-up → Pipeline Update.",
     "author": "OpenPaper AI", "tags": ["sales", "outreach", "email", "pipeline"],
     "downloads": 1200, "rating": 4.6, "permissions": ["memory:read", "agent:execute", "task:read", "task:write"],
     "dependencies": ["agent-sales", "agent-email"], "config_schema": {},
     "readme": "# Sales Outreach Workflow\\n\\nAutomated multi-channel sales outreach with qualification and follow-up."},
    {"id": "wf-content", "name": "Content Creation Workflow", "item_type": "workflow", "version": "1.0.0",
     "description": "Content pipeline: Research → Outline → Draft → Review → Publish with SEO optimization.",
     "author": "OpenPaper AI", "tags": ["content", "seo", "marketing", "writing"],
     "downloads": 890, "rating": 4.5, "permissions": ["memory:read", "memory:write", "agent:execute", "bus:publish"],
     "dependencies": ["agent-research", "agent-seo"], "config_schema": {},
     "readme": "# Content Creation Workflow\\n\\nEnd-to-end content creation with research, drafting, SEO optimization, and publishing."},

    # ── Tools ──
    {"id": "tool-web-scraper", "name": "Web Scraper", "item_type": "tool", "version": "1.0.0",
     "description": "Extract data from websites with configurable selectors, pagination, and rate limiting.",
     "author": "OpenPaper AI", "tags": ["scraping", "web", "data", "extraction"],
     "downloads": 3400, "rating": 4.8, "permissions": ["network"],
     "dependencies": [], "config_schema": {},
     "readme": "# Web Scraper Tool\\n\\nExtract structured data from websites with CSS selectors and pagination support."},
    {"id": "tool-csv-export", "name": "CSV/Excel Exporter", "item_type": "tool", "version": "1.0.0",
     "description": "Export any data to CSV, Excel, or JSON format with customizable column mapping.",
     "author": "OpenPaper AI", "tags": ["export", "csv", "excel", "data"],
     "downloads": 2100, "rating": 4.6, "permissions": ["memory:read"],
     "dependencies": [], "config_schema": {},
     "readme": "# CSV/Excel Exporter\\n\\nExport data to CSV, Excel, or JSON with customizable formatting."},
    {"id": "tool-pdf-gen", "name": "PDF Generator", "item_type": "tool", "version": "1.0.0",
     "description": "Generate PDF reports and documents from templates with dynamic data injection.",
     "author": "OpenPaper AI", "tags": ["pdf", "report", "document", "template"],
     "downloads": 1800, "rating": 4.7, "permissions": [],
     "dependencies": [], "config_schema": {},
     "readme": "# PDF Generator\\n\\nGenerate professional PDF reports and documents from templates."},
    {"id": "tool-slack", "name": "Slack Notifier", "item_type": "tool", "version": "1.0.0",
     "description": "Send notifications and alerts to Slack channels with customizable message templates.",
     "author": "OpenPaper AI", "tags": ["slack", "notification", "messaging", "integration"],
     "downloads": 1500, "rating": 4.5, "permissions": ["network"],
     "dependencies": [], "config_schema": {},
     "readme": "# Slack Notifier\\n\\nSend automated notifications to Slack channels from any workflow or agent."},
    {"id": "tool-data-analyzer", "name": "Data Analyzer", "item_type": "tool", "version": "1.0.0",
     "description": "Analyze datasets with statistical functions, visualization, and anomaly detection.",
     "author": "OpenPaper AI", "tags": ["analysis", "data", "statistics", "visualization"],
     "downloads": 1100, "rating": 4.4, "permissions": ["memory:read"],
     "dependencies": [], "config_schema": {},
     "readme": "# Data Analyzer\\n\\nAnalyze datasets with statistics, anomaly detection, and visualization."},

    # ── Providers ──
    {"id": "prov-deepseek", "name": "DeepSeek Provider", "item_type": "provider", "version": "1.0.0",
     "description": "DeepSeek AI provider integration for chat and embedding models via API.",
     "author": "OpenPaper AI", "tags": ["deepseek", "china", "llm", "chat"],
     "downloads": 890, "rating": 4.3, "permissions": ["network", "provider:read", "provider:write"],
     "dependencies": [], "config_schema": {},
     "readme": "# DeepSeek Provider\\n\\nIntegrate DeepSeek AI models for chat completions and embeddings."},
    {"id": "prov-grok", "name": "Grok Provider", "item_type": "provider", "version": "1.0.0",
     "description": "xAI Grok provider integration for chat completions with real-time knowledge.",
     "author": "OpenPaper AI", "tags": ["grok", "xai", "llm", "chat"],
     "downloads": 670, "rating": 4.4, "permissions": ["network", "provider:read", "provider:write"],
     "dependencies": [], "config_schema": {},
     "readme": "# Grok Provider\\n\\nIntegrate xAI Grok models for chat completions."},
    {"id": "prov-nim", "name": "NVIDIA NIM Provider", "item_type": "provider", "version": "1.0.0",
     "description": "NVIDIA NIM provider for accelerated inference on NVIDIA GPUs.",
     "author": "OpenPaper AI", "tags": ["nvidia", "nim", "gpu", "inference"],
     "downloads": 450, "rating": 4.6, "permissions": ["network", "provider:read", "provider:write"],
     "dependencies": [], "config_schema": {},
     "readme": "# NVIDIA NIM Provider\\n\\nAccelerated model inference with NVIDIA NIM microservices."},
    {"id": "prov-gemini", "name": "Gemini Provider", "item_type": "provider", "version": "1.0.0",
     "description": "Google Gemini provider for multimodal AI chat and analysis capabilities.",
     "author": "OpenPaper AI", "tags": ["gemini", "google", "multimodal", "llm"],
     "downloads": 1200, "rating": 4.7, "permissions": ["network", "provider:read", "provider:write"],
     "dependencies": [], "config_schema": {},
     "readme": "# Gemini Provider\\n\\nIntegrate Google Gemini models for multimodal chat and analysis."},
    {"id": "prov-openrouter", "name": "OpenRouter Provider", "item_type": "provider", "version": "1.0.0",
     "description": "OpenRouter provider for unified access to 100+ models across providers.",
     "author": "OpenPaper AI", "tags": ["openrouter", "multi-provider", "llm", "unified"],
     "downloads": 2100, "rating": 4.8, "permissions": ["network", "provider:read", "provider:write"],
     "dependencies": [], "config_schema": {},
     "readme": "# OpenRouter Provider\\n\\nUnified access to 100+ AI models through a single API."},
]

CATEGORIES = ["agents", "workflows", "tools", "providers"]


def _get_item_type_filter(category: str | None) -> MarketplaceItemType | None:
    mapping = {
        "agents": MarketplaceItemType.AGENT,
        "workflows": MarketplaceItemType.WORKFLOW,
        "tools": MarketplaceItemType.TOOL,
        "providers": MarketplaceItemType.PROVIDER,
    }
    return mapping.get(category) if category else None


# ── Endpoints ───────────────────────────────────────────────────────

@router.get("", response_model=MarketplaceListResponse)
async def list_marketplace(
    category: str | None = Query(None, pattern="^(agents|workflows|tools|providers)$"),
    search: str | None = Query(None, min_length=1),
    featured: bool = Query(False),
    trending: bool = Query(False),
    recently_added: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = list(BUILTIN_ITEMS)

    # Get installed items for status
    result = await db.execute(
        select(InstalledMarketplaceItem).where(
            InstalledMarketplaceItem.user_id == current_user.id
        )
    )
    installed = {i.item_id: i.status.value for i in result.scalars().all()}

    # Filter by category
    if category:
        type_filter = _get_item_type_filter(category)
        if type_filter:
            items = [i for i in items if i["item_type"] == type_filter.value]

    # Search
    if search:
        q = search.lower()
        items = [
            i for i in items
            if q in i["name"].lower()
            or q in i["description"].lower()
            or any(q in t.lower() for t in i["tags"])
            or q in i["author"].lower()
        ]

    # Sort
    if featured:
        items = sorted(items, key=lambda i: i["rating"], reverse=True)[:6]
    elif trending:
        items = sorted(items, key=lambda i: i["downloads"], reverse=True)[:8]
    elif recently_added:
        items = items[:8]

    response_items = []
    for item in items:
        response_items.append(MarketplaceItemResponse(
            **item,
            install_status=installed.get(item["id"], "not_installed"),
        ))

    return MarketplaceListResponse(
        items=response_items,
        total=len(response_items),
        categories=CATEGORIES,
    )


@router.get("/{item_id}", response_model=MarketplaceItemResponse)
async def get_marketplace_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for item in BUILTIN_ITEMS:
        if item["id"] == item_id:
            result = await db.execute(
                select(InstalledMarketplaceItem).where(
                    InstalledMarketplaceItem.item_id == item_id,
                    InstalledMarketplaceItem.user_id == current_user.id,
                )
            )
            installed = result.scalar_one_or_none()
            return MarketplaceItemResponse(
                **item,
                install_status=installed.status.value if installed else "not_installed",
            )
    raise NotFoundError(f"Marketplace item '{item_id}' not found")


@router.get("/installed/list", response_model=list[InstalledItemResponse])
async def list_installed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InstalledMarketplaceItem)
        .where(InstalledMarketplaceItem.user_id == current_user.id)
        .order_by(InstalledMarketplaceItem.installed_at.desc())
    )
    return [InstalledItemResponse.model_validate(i) for i in result.scalars().all()]


@router.post("/install", response_model=InstallResponse)
async def install_item(
    body: InstallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = None
    for bi in BUILTIN_ITEMS:
        if bi["id"] == body.item_id:
            item = bi
            break
    if not item:
        raise NotFoundError(f"Item '{body.item_id}' not found in marketplace")

    # Check not already installed
    result = await db.execute(
        select(InstalledMarketplaceItem).where(
            InstalledMarketplaceItem.item_id == body.item_id,
            InstalledMarketplaceItem.user_id == current_user.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing and existing.status == InstallStatus.INSTALLED:
        raise ConflictError(f"Item '{body.item_id}' is already installed")

    # Check dependencies
    deps = item.get("dependencies", [])
    for dep_id in deps:
        dep_result = await db.execute(
            select(InstalledMarketplaceItem).where(
                InstalledMarketplaceItem.item_id == dep_id,
                InstalledMarketplaceItem.user_id == current_user.id,
                InstalledMarketplaceItem.status == InstallStatus.INSTALLED,
            )
        )
        if not dep_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Missing dependency: '{dep_id}' must be installed first",
            )

    # Integrate with plugin registry for tool/provider/workflow types
    registry = get_plugin_registry()
    plugin_type_map = {
        "agent": PluginType.AGENT,
        "workflow": PluginType.WORKFLOW,
        "tool": PluginType.TOOL,
        "provider": PluginType.PROVIDER,
    }
    ptype = plugin_type_map.get(item["item_type"])
    if ptype:
        manifest = PluginManifest(
            name=item["name"],
            version=item["version"],
            description=item["description"],
            author=item["author"],
            plugin_type=ptype,
            permissions=[PluginPermission(p) for p in item.get("permissions", [])],
            dependencies=item.get("dependencies", []),
        )
        try:
            registry._manifests[item["id"]] = manifest
            registry._status[item["id"]] = "loaded"
            registry._loaded_at[item["id"]] = datetime.now(UTC).isoformat()
        except Exception as e:
            logger.error("Failed to register plugin for %s: %s", item["id"], e)

    # Create or update installation record
    if existing:
        existing.status = InstallStatus.INSTALLED
        existing.version = item["version"]
        existing.updated_at = datetime.now(UTC)
    else:
        install = InstalledMarketplaceItem(
            item_id=item["id"],
            name=item["name"],
            item_type=MarketplaceItemType(item["item_type"]),
            version=item["version"],
            status=InstallStatus.INSTALLED,
            author=item["author"],
            description=item["description"],
            permissions=item.get("permissions", []),
            dependencies=item.get("dependencies", []),
            config=body.config,
            user_id=current_user.id,
        )
        db.add(install)

    await db.commit()
    return InstallResponse(
        success=True,
        item_id=item["id"],
        status="installed",
        message=f"{item['name']} v{item['version']} installed successfully",
        permissions_requested=item.get("permissions", []),
    )


@router.post("/{item_id}/uninstall", response_model=InstallResponse)
async def uninstall_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InstalledMarketplaceItem).where(
            InstalledMarketplaceItem.item_id == item_id,
            InstalledMarketplaceItem.user_id == current_user.id,
        )
    )
    install = result.scalar_one_or_none()
    if not install:
        raise NotFoundError(f"Item '{item_id}' is not installed")

    # Remove from plugin registry
    registry = get_plugin_registry()
    if item_id in registry._manifests:
        del registry._manifests[item_id]
    if item_id in registry._status:
        del registry._status[item_id]
    if item_id in registry._loaded_at:
        del registry._loaded_at[item_id]

    install.status = InstallStatus.UNINSTALLED
    await db.commit()
    return InstallResponse(
        success=True,
        item_id=item_id,
        status="uninstalled",
        message=f"'{install.name}' uninstalled successfully",
    )


@router.post("/{item_id}/update", response_model=InstallResponse)
async def update_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = None
    for bi in BUILTIN_ITEMS:
        if bi["id"] == item_id:
            item = bi
            break
    if not item:
        raise NotFoundError(f"Item '{item_id}' not found in marketplace")

    result = await db.execute(
        select(InstalledMarketplaceItem).where(
            InstalledMarketplaceItem.item_id == item_id,
            InstalledMarketplaceItem.user_id == current_user.id,
        )
    )
    install = result.scalar_one_or_none()
    if not install:
        raise NotFoundError(f"Item '{item_id}' is not installed")

    old_version = install.version
    install.version = item["version"]
    install.status = InstallStatus.INSTALLED
    install.updated_at = datetime.now(UTC)
    await db.commit()

    return InstallResponse(
        success=True,
        item_id=item_id,
        status="updated",
        message=f"'{item['name']}' updated from v{old_version} to v{item['version']}",
    )
