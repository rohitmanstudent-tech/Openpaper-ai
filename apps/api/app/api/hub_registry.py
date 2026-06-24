"""OpenPaper Hub Registry API — remote package registry with
search, publish, versioning, dependency resolution, signature verification,
ratings, and local marketplace sync."""

import contextlib
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.hub_resolver import DependencyGraph, LockEntry, Lockfile, Version, find_best_match
from app.core.hub_signer import compute_checksum, compute_package_hash, verify_signature
from app.core.plugin_registry import get_plugin_registry
from app.core.security import get_current_user, get_current_user_optional
from app.database import get_db
from app.models import User
from app.models.hub_registry import (
    PackageType,
    PackageVisibility,
    PublisherKey,
    RegistryPackage,
    RegistryPackageVersion,
    RegistryRating,
    RegistrySyncLog,
)
from app.schemas.hub_registry import (
    InstallResolution,
    PackageDetailResponse,
    PackageSearchItem,
    PackageSearchResponse,
    PackageVersionResponse,
    PublishRequest,
    PublishResponse,
    RatingRequest,
    RatingResponse,
    ResolveResponse,
    SyncResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hub", tags=["hub"])


# ── Search / List ───────────────────────────────────────────────────


@router.get("/packages", response_model=PackageSearchResponse)
async def search_packages(
    query: str | None = Query(None, min_length=1),
    package_type: str | None = Query(None, pattern="^(agent|workflow|tool|provider)$"),
    sort: str = Query("downloads", pattern="^(downloads|rating|name|created|updated)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    visibility: str | None = Query(None, pattern="^(public|private)$"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user_optional),
):
    stmt = select(RegistryPackage)

    if query:
        q = f"%{query}%"
        stmt = stmt.where(
            or_(
                RegistryPackage.name.ilike(q),
                RegistryPackage.description.ilike(q),
                RegistryPackage.author.ilike(q),
                RegistryPackage.tags.as_string().ilike(q),
            )
        )

    if package_type:
        try:
            pt = PackageType(package_type)
            stmt = stmt.where(RegistryPackage.package_type == pt)
        except ValueError:
            pass

    if visibility:
        try:
            pv = PackageVisibility(visibility)
            stmt = stmt.where(RegistryPackage.visibility == pv)
        except ValueError:
            pass

    stmt = stmt.where(RegistryPackage.visibility == PackageVisibility.PUBLIC)

    sort_col = {
        "downloads": RegistryPackage.downloads,
        "rating": RegistryPackage.rating_sum / func.nullif(RegistryPackage.rating_count, 0),
        "name": RegistryPackage.name,
        "created": RegistryPackage.created_at,
        "updated": RegistryPackage.updated_at,
    }.get(sort, RegistryPackage.downloads)

    order_fn = desc if order == "desc" else asc
    stmt = stmt.order_by(order_fn(sort_col))

    total_q = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    packages = result.scalars().all()

    items = []
    for pkg in packages:
        items.append(
            PackageSearchItem(
                id=pkg.package_id,
                name=pkg.name,
                description=pkg.description,
                package_type=pkg.package_type.value,
                author=pkg.author,
                current_version=pkg.current_version,
                downloads=pkg.downloads,
                average_rating=pkg.average_rating,
                rating_count=pkg.rating_count,
                verified_publisher=pkg.verified_publisher,
                tags=pkg.tags or [],
            )
        )

    return PackageSearchResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/packages/{package_id}", response_model=PackageDetailResponse)
async def get_package_detail(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user_optional),
):
    result = await db.execute(select(RegistryPackage).where(RegistryPackage.package_id == package_id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise NotFoundError(f"Package '{package_id}' not found in registry")

    versions = []
    for v in pkg.versions:
        versions.append(
            PackageVersionResponse(
                version=v.version,
                checksum_sha256=v.checksum_sha256,
                signature=v.signature,
                signature_key_id=v.signature_key_id,
                dependencies=v.dependencies or [],
                changelog=v.changelog,
                published_at=v.published_at,
            )
        )

    return PackageDetailResponse(
        id=pkg.package_id,
        name=pkg.name,
        description=pkg.description,
        package_type=pkg.package_type.value,
        author=pkg.author,
        current_version=pkg.current_version,
        visibility=pkg.visibility.value,
        downloads=pkg.downloads,
        average_rating=pkg.average_rating,
        rating_count=pkg.rating_count,
        verified_publisher=pkg.verified_publisher,
        tags=pkg.tags or [],
        homepage=pkg.homepage,
        repository=pkg.repository,
        readme=pkg.readme,
        versions=versions,
        created_at=pkg.created_at,
        updated_at=pkg.updated_at,
    )


# ── Publish ─────────────────────────────────────────────────────────


@router.post("/packages", response_model=PublishResponse)
async def publish_package(
    body: PublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    manifest = body.manifest
    pkg_id = manifest.name.lower().replace(" ", "-")

    existing = await db.execute(select(RegistryPackage).where(RegistryPackage.package_id == pkg_id))
    existing_pkg = existing.scalar_one_or_none()

    if existing_pkg:
        if existing_pkg.publisher_id != current_user.id:
            raise ConflictError(f"Package '{pkg_id}' already exists and you are not the publisher")
        return await _publish_new_version(db, existing_pkg, body, current_user)

    pkg_type = PackageType.AGENT
    try:
        pkg_type = PackageType(manifest.package_type)
    except ValueError:
        raise ValidationError(f"Invalid package type: {manifest.package_type}") from None

    visibility = PackageVisibility.PUBLIC
    with contextlib.suppress(ValueError):
        visibility = PackageVisibility(body.visibility)

    checksum = compute_checksum(manifest.model_dump())

    sig_verified = False
    if body.signature and body.signature_key_id:
        key_result = await db.execute(
            select(PublisherKey).where(
                PublisherKey.key_id == body.signature_key_id,
                PublisherKey.is_active,
            )
        )
        pub_key = key_result.scalar_one_or_none()
        if pub_key:
            sig_verified = verify_signature(manifest.model_dump(), body.signature, pub_key.public_key)

    pkg = RegistryPackage(
        package_id=pkg_id,
        name=manifest.name,
        description=manifest.description,
        package_type=pkg_type,
        author=manifest.author or current_user.username,
        publisher_id=current_user.id,
        current_version=manifest.version,
        visibility=visibility,
        tags=manifest.tags,
        homepage=manifest.homepage,
        repository=manifest.repository,
        readme=manifest.readme,
    )
    db.add(pkg)
    await db.flush()

    version = RegistryPackageVersion(
        package_id=pkg.id,
        version=manifest.version,
        manifest=manifest.model_dump(),
        signature=body.signature or "",
        signature_key_id=body.signature_key_id or "",
        checksum_sha256=checksum,
        content_hash=compute_package_hash(body.source_archive) if body.source_archive else checksum,
        dependencies=manifest.dependencies,
        changelog=body.changelog,
    )
    db.add(version)

    try:
        registry = get_plugin_registry()
        from app.models.plugin import PluginManifest, PluginPermission, PluginType

        pt_map = {
            "agent": PluginType.AGENT,
            "workflow": PluginType.WORKFLOW,
            "tool": PluginType.TOOL,
            "provider": PluginType.PROVIDER,
        }
        ptype = pt_map.get(manifest.package_type)
        if ptype:
            pm = PluginManifest(
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                author=manifest.author,
                plugin_type=ptype,
                permissions=[
                    PluginPermission(p) for p in manifest.permissions if p in [pp.value for pp in PluginPermission]
                ],
                dependencies=manifest.dependencies,
            )
            registry.register_manifest(pkg_id, pm)
            logger.info("Registered published package '%s' in plugin registry", pkg_id)
    except Exception as e:
        logger.warning("Failed to register in plugin registry: %s", e)

    await db.commit()
    return PublishResponse(
        success=True,
        package_id=pkg_id,
        version=manifest.version,
        message=f"Published {manifest.name} v{manifest.version}",
        signature_verified=sig_verified,
    )


async def _publish_new_version(
    db: AsyncSession,
    pkg: RegistryPackage,
    body: PublishRequest,
    user: User,
) -> PublishResponse:
    manifest = body.manifest

    if Version(manifest.version) <= Version(pkg.current_version):
        raise ValidationError(f"New version {manifest.version} must be greater than current {pkg.current_version}")

    for existing_v in pkg.versions:
        if existing_v.version == manifest.version:
            raise ConflictError(f"Version {manifest.version} already exists for '{pkg.package_id}'")

    checksum = compute_checksum(manifest.model_dump())

    sig_verified = False
    if body.signature and body.signature_key_id:
        key_result = await db.execute(
            select(PublisherKey).where(
                PublisherKey.key_id == body.signature_key_id,
                PublisherKey.is_active,
            )
        )
        pub_key = key_result.scalar_one_or_none()
        if pub_key:
            sig_verified = verify_signature(manifest.model_dump(), body.signature, pub_key.public_key)

    version = RegistryPackageVersion(
        package_id=pkg.id,
        version=manifest.version,
        manifest=manifest.model_dump(),
        signature=body.signature or "",
        signature_key_id=body.signature_key_id or "",
        checksum_sha256=checksum,
        content_hash=compute_package_hash(body.source_archive) if body.source_archive else checksum,
        dependencies=manifest.dependencies,
        changelog=body.changelog,
    )
    db.add(version)

    pkg.current_version = manifest.version
    pkg.updated_at = datetime.now(UTC)

    if manifest.description:
        pkg.description = manifest.description
    if manifest.tags:
        pkg.tags = list(set(pkg.tags or []) | set(manifest.tags))
    if manifest.readme:
        pkg.readme = manifest.readme

    await db.commit()
    return PublishResponse(
        success=True,
        package_id=pkg.package_id,
        version=manifest.version,
        message=f"Published {manifest.name} v{manifest.version}",
        signature_verified=sig_verified,
    )


# ── Unpublish ───────────────────────────────────────────────────────


@router.delete("/packages/{package_id}", response_model=dict)
async def unpublish_package(
    package_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RegistryPackage).where(RegistryPackage.package_id == package_id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise NotFoundError(f"Package '{package_id}' not found")
    if pkg.publisher_id != current_user.id:
        from app.core.exceptions import PermissionDeniedError

        raise PermissionDeniedError("You can only unpublish your own packages")

    registry = get_plugin_registry()
    registry.unregister_manifest(package_id)

    await db.delete(pkg)
    await db.commit()
    return {"success": True, "message": f"Unpublished '{package_id}'"}


# ── Download / Resolve ──────────────────────────────────────────────


@router.get("/packages/{package_id}/resolve", response_model=ResolveResponse)
async def resolve_package(
    package_id: str,
    version: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user_optional),
):
    result = await db.execute(select(RegistryPackage).where(RegistryPackage.package_id == package_id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise NotFoundError(f"Package '{package_id}' not found")

    available_versions = [v.version for v in pkg.versions]
    target_version = version or pkg.current_version

    resolved = find_best_match(available_versions, target_version)
    if not resolved:
        raise NotFoundError(f"No version of '{package_id}' satisfies constraint '{target_version}'")

    version_obj = None
    for v in pkg.versions:
        if v.version == resolved:
            version_obj = v
            break

    if not version_obj:
        raise NotFoundError(f"Version {resolved} not found for '{package_id}'")

    manifest_dict = version_obj.manifest or {}
    permissions = manifest_dict.get("permissions", [])

    graph = DependencyGraph()
    graph.add_package(
        pkg.package_id, resolved, version_obj.dependencies or {}, {"name": pkg.name, "type": pkg.package_type.value}
    )

    dep_chain: list[InstallResolution] = []
    dep_names = version_obj.dependencies or []
    for dep_id in dep_names:
        dep_result = await db.execute(select(RegistryPackage).where(RegistryPackage.package_id == dep_id))
        dep_pkg = dep_result.scalar_one_or_none()
        if dep_pkg:
            dep_version = dep_pkg.current_version
            dep_manifest = {}
            if dep_pkg.versions:
                dep_manifest = dep_pkg.versions[0].manifest or {}
            dep_chain.append(
                InstallResolution(
                    package_id=dep_id,
                    name=dep_pkg.name,
                    version=dep_version,
                    manifest=dep_manifest,
                    checksum_sha256=dep_pkg.versions[0].checksum_sha256 if dep_pkg.versions else "",
                    permissions_requested=dep_manifest.get("permissions", []),
                )
            )

    resolution = InstallResolution(
        package_id=pkg.package_id,
        name=pkg.name,
        version=resolved,
        dependencies=version_obj.dependencies or [],
        manifest=manifest_dict,
        signature=version_obj.signature,
        signature_key_id=version_obj.signature_key_id,
        checksum_sha256=version_obj.checksum_sha256,
        permissions_requested=permissions,
    )

    lockfile = Lockfile()
    lockfile.add_entry(
        LockEntry(
            name=pkg.package_id,
            version=target_version,
            resolved_version=resolved,
            dependencies=version_obj.dependencies or [],
            checksum=version_obj.checksum_sha256,
        )
    )
    for dep in dep_chain:
        lockfile.add_entry(
            LockEntry(
                name=dep.package_id,
                version="*",
                resolved_version=dep.version,
                dependencies=dep.dependencies,
                checksum=dep.checksum_sha256,
            )
        )

    return ResolveResponse(
        success=True,
        package_id=pkg.package_id,
        version=resolved,
        resolution=resolution,
        dependency_chain=dep_chain,
    )


# ── Ratings ─────────────────────────────────────────────────────────


@router.post("/packages/{package_id}/ratings", response_model=RatingResponse)
async def rate_package(
    package_id: str,
    body: RatingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RegistryPackage).where(RegistryPackage.package_id == package_id))
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise NotFoundError(f"Package '{package_id}' not found")

    existing_q = await db.execute(
        select(RegistryRating).where(
            RegistryRating.package_id == pkg.id,
            RegistryRating.user_id == current_user.id,
        )
    )
    existing = existing_q.scalar_one_or_none()
    if existing:
        pkg.rating_sum -= existing.rating
        pkg.rating_sum += body.rating
        existing.rating = body.rating
        existing.review = body.review
    else:
        rating = RegistryRating(
            package_id=pkg.id,
            user_id=current_user.id,
            rating=body.rating,
            review=body.review,
        )
        db.add(rating)
        pkg.rating_sum += body.rating
        pkg.rating_count += 1

    await db.commit()
    return RatingResponse(
        success=True,
        new_average=pkg.average_rating,
        total_ratings=pkg.rating_count,
    )


# ── Publisher Keys ──────────────────────────────────────────────────


@router.post("/keys", response_model=dict)
async def register_publisher_key(
    key_id: str,
    public_key: str,
    algorithm: str = "ed25519",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(PublisherKey).where(
            PublisherKey.key_id == key_id,
            PublisherKey.is_active,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Key '{key_id}' already exists")

    pk = PublisherKey(
        user_id=current_user.id,
        key_id=key_id,
        public_key=public_key,
        algorithm=algorithm,
    )
    db.add(pk)
    await db.commit()
    return {"success": True, "key_id": key_id, "message": "Publisher key registered"}


@router.delete("/keys/{key_id}", response_model=dict)
async def revoke_publisher_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PublisherKey).where(
            PublisherKey.key_id == key_id,
        )
    )
    pk = result.scalar_one_or_none()
    if not pk:
        raise NotFoundError(f"Key '{key_id}' not found")
    if pk.user_id != current_user.id:
        from app.core.exceptions import PermissionDeniedError

        raise PermissionDeniedError("You can only revoke your own keys")

    pk.is_active = False
    pk.revoked_at = datetime.now(UTC)
    await db.commit()
    return {"success": True, "message": f"Key '{key_id}' revoked"}


# ── Sync: Registry ↔ Local Marketplace ─────────────────────────────


@router.post("/sync", response_model=SyncResponse)
async def sync_registry(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.marketplace import InstalledMarketplaceItem, InstallStatus, MarketplaceItemType

    sync_log = RegistrySyncLog(status="in_progress")
    db.add(sync_log)
    await db.flush()

    errors: list[str] = []
    synced = 0
    added = 0
    updated = 0

    result = await db.execute(select(RegistryPackage).where(RegistryPackage.visibility == PackageVisibility.PUBLIC))
    remote_packages = result.scalars().all()

    for rp in remote_packages:
        try:
            existing_q = await db.execute(
                select(InstalledMarketplaceItem).where(
                    InstalledMarketplaceItem.item_id == rp.package_id,
                    InstalledMarketplaceItem.user_id == current_user.id,
                )
            )
            existing = existing_q.scalar_one_or_none()

            mt_map = {
                PackageType.AGENT: MarketplaceItemType.AGENT,
                PackageType.WORKFLOW: MarketplaceItemType.WORKFLOW,
                PackageType.TOOL: MarketplaceItemType.TOOL,
                PackageType.PROVIDER: MarketplaceItemType.PROVIDER,
            }
            mt = mt_map.get(rp.package_type, MarketplaceItemType.TOOL)

            if existing:
                if Version(rp.current_version) > Version(existing.version):
                    existing.version = rp.current_version
                    existing.status = InstallStatus.UPDATE_AVAILABLE
                    existing.updated_at = datetime.now(UTC)
                    updated += 1
            else:
                install = InstalledMarketplaceItem(
                    item_id=rp.package_id,
                    name=rp.name,
                    item_type=mt,
                    version=rp.current_version,
                    status=InstallStatus.NOT_INSTALLED,
                    author=rp.author,
                    description=rp.description,
                    permissions=[],
                    dependencies=[],
                    config={},
                    user_id=current_user.id,
                )
                db.add(install)
                added += 1

            synced += 1
        except Exception as e:
            errors.append(f"Failed to sync '{rp.package_id}': {e}")

    sync_log.status = "completed"
    sync_log.packages_synced = synced
    sync_log.packages_added = added
    sync_log.packages_updated = updated
    sync_log.errors = errors
    sync_log.completed_at = datetime.now(UTC)

    await db.commit()
    return SyncResponse(
        success=True,
        message=f"Synced {synced} packages ({added} new, {updated} updated)",
        packages_synced=synced,
        packages_added=added,
        packages_updated=updated,
        errors=errors,
    )


@router.get("/sync/status", response_model=dict)
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RegistrySyncLog).order_by(desc(RegistrySyncLog.started_at)).limit(5))
    logs = result.scalars().all()
    return {
        "success": True,
        "recent_syncs": [
            {
                "id": log.id,
                "status": log.status,
                "packages_synced": log.packages_synced,
                "packages_added": log.packages_added,
                "packages_updated": log.packages_updated,
                "errors": log.errors,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            }
            for log in logs
        ],
    }


# ── Stats ───────────────────────────────────────────────────────────


@router.get("/stats", response_model=dict)
async def get_registry_stats(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user_optional),
):
    total_q = await db.execute(select(func.count()).select_from(RegistryPackage))
    total_packages = total_q.scalar() or 0

    type_q = await db.execute(select(RegistryPackage.package_type, func.count()).group_by(RegistryPackage.package_type))
    type_breakdown = {row[0].value: row[1] for row in type_q.all()}

    verified_q = await db.execute(select(func.count()).where(RegistryPackage.verified_publisher))
    verified = verified_q.scalar() or 0

    return {
        "success": True,
        "total_packages": total_packages,
        "type_breakdown": type_breakdown,
        "verified_publishers": verified,
        "registry_url": "https://hub.openpaper.ai/api/v1",
    }
