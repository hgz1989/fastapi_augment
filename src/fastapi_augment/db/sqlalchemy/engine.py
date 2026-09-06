"""
@Author         : hangu
@CreateDate     : 2026/8/31
@Description    : SQLAlchemy async engine factory, supporting single / master-replica / cluster topologies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import cycle
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


# ── Configuration Models ─────────────────────────────────────────────────────


@dataclass
class NodeConfig:
    """Single database node configuration.

    Args:
        url: Async SQLAlchemy connection URL, e.g. ``postgresql+asyncpg://user:pass@host/db``.
        pool_size: Connection pool size (0 = unlimited).
        max_overflow: Max connections allowed beyond *pool_size*.
        pool_timeout: Seconds to wait for a connection from the pool.
        pool_recycle: Recycle connections after N seconds (-1 = disable).
        pool_pre_ping: Emit a test statement on checkout to verify liveness.
        echo: Log all SQL statements.
        connect_args: Extra arguments passed to the DBAPI ``connect()``.
    """

    url: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 30.0
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    echo: bool = False
    connect_args: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.url:
            raise ValueError('url must not be empty')
        if self.pool_size < 0:
            raise ValueError(f'pool_size must be >= 0, got {self.pool_size}')
        if self.max_overflow < 0:
            raise ValueError(f'max_overflow must be >= 0, got {self.max_overflow}')
        if self.pool_timeout < 0:
            raise ValueError(f'pool_timeout must be >= 0, got {self.pool_timeout}')
        if self.pool_recycle < -1:
            raise ValueError(f'pool_recycle must be >= -1, got {self.pool_recycle}')


@dataclass
class ClusterTopology:
    """
    Database cluster topology.

    Supports three deployment patterns::

        Single        : only ``primary`` is set
        Master-Replica: ``primary`` + ``replicas``
        Cluster       : ``primary`` + ``replicas`` + ``readonly``

    Read routing priority: replicas -> readonly -> primary (fallback).
    """

    primary: NodeConfig
    replicas: list[NodeConfig] = field(default_factory=list)
    readonly: list[NodeConfig] = field(default_factory=list)

    @property
    def is_single(self) -> bool:
        """Indicates whether the topology consists of a single primary node (no replicas or readonly nodes).

        Returns:
            True if the topology is single, False otherwise.
        """
        return not self.replicas and not self.readonly

    @property
    def is_master_replica(self) -> bool:
        """Indicates whether the topology consists of a single primary node and one or more replicas (no readonly nodes).

        Returns:
            True if the topology is master-replica, False otherwise.
        """
        return bool(self.replicas) and not self.readonly

    @property
    def is_cluster(self) -> bool:
        """Indicates whether the topology consists of a single primary node, one or more replicas, and one or more readonly nodes.

        Returns:
            True if the topology is a cluster, False otherwise.
        """
        return bool(self.replicas) or bool(self.readonly)

    def get_all_read_sources(self) -> list[NodeConfig]:
        """Return all nodes eligible for read traffic (replicas first, then readonly).

        Returns:
            A list of node configurations.
        """
        return [*self.replicas, *self.readonly]


# ── Engine Manager ───────────────────────────────────────────────────────────


class EngineManager:
    """
    Manages the full lifecycle of async SQLAlchemy engines.

    Usage::

        topology = ClusterTopology(
            primary=NodeConfig(url='postgresql+asyncpg://...'),
            replicas=[NodeConfig(url='postgresql+asyncpg://replica-1/...')],
        )
        manager = EngineManager(topology)
        manager.start()

        write_engine = manager.write_engine
        read_engine  = manager.next_read_engine()  # round-robin

        await manager.dispose()
    """

    def __init__(self, topology: ClusterTopology) -> None:
        self._topology = topology
        self._engines: dict[str, AsyncEngine] = {}
        self._write_key: str = 'primary'
        self._read_keys: list[str] = []
        self._read_cycle: cycle[str] | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────

    def start(self) -> EngineManager:
        """Create all engines based on the topology. Returns *self* for chaining.

        Returns:
            The engine manager instance itself, for method chaining.
        """
        self._engines[self._write_key] = self._create_engine(self._topology.primary)

        read_sources = self._topology.get_all_read_sources()
        for idx, node in enumerate(read_sources):
            key = f'read_{idx}'
            self._engines[key] = self._create_engine(node)
            self._read_keys.append(key)

        if self._read_keys:
            self._read_cycle = cycle(self._read_keys)

        return self

    async def dispose(self) -> None:
        """Dispose all engine connection pools gracefully."""
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._read_keys.clear()
        self._read_cycle = None

    # ── Engine Access ────────────────────────────────────────────────────

    @property
    def write_engine(self) -> AsyncEngine:
        """The primary engine used for all write operations.

        Returns:
            The primary async SQLAlchemy engine.
        """
        return self._engines[self._write_key]

    def next_read_engine(self) -> AsyncEngine:
        """Return the next read engine via round-robin; falls back to the write engine.

        Returns:
            An async SQLAlchemy engine.
        """
        if self._read_cycle is not None:
            return self._engines[next(self._read_cycle)]
        return self.write_engine

    def get_engine(self, name: str) -> AsyncEngine:
        """Get a specific engine by its key (e.g. ``'primary'``, ``'read_0'``).

        Args:
            name: Engine key.

        Returns:
            An async SQLAlchemy engine.
        """
        return self._engines[name]

    @property
    def engines(self) -> dict[str, AsyncEngine]:
        """All engines managed by the engine manager.

        Returns:
            A dictionary of engine key -> async SQLAlchemy engine.
        """
        return dict(self._engines)

    @property
    def topology(self) -> ClusterTopology:
        """The database topology configuration.

        Returns:
            A ClusterTopology instance.
        """
        return self._topology

    # ── Internal ─────────────────────────────────────────────────────────

    @staticmethod
    def _create_engine(node: NodeConfig) -> AsyncEngine:
        """Create an async SQLAlchemy engine based on the given node configuration.

        Args:
            node: Database node configuration.

        Returns:
            An async SQLAlchemy engine.
        """
        return create_async_engine(
            node.url,
            pool_size=node.pool_size,
            max_overflow=node.max_overflow,
            pool_timeout=node.pool_timeout,
            pool_recycle=node.pool_recycle,
            pool_pre_ping=node.pool_pre_ping,
            echo=node.echo,
            connect_args=node.connect_args,
        )
