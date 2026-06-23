"""Tests for the Plugin System module."""

import os
import sys
import tempfile

import pytest
import yaml

from app.core.plugin_registry import PluginRegistry, PluginSandbox, set_plugin_registry
from app.models.plugin import (
    PluginCreate,
    PluginHook,
    PluginManifest,
    PluginPermission,
    PluginResponse,
    PluginStatus,
    PluginType,
)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))


_TOOL_SOURCE = '''
from app.core.plugin_base import ToolPlugin
class TestToolPlugin(ToolPlugin):
    name = "test_tool"
    version = "1.0.0"
    description = "A test tool plugin"
    async def execute(self, params: dict) -> dict:
        return {"result": f"executed: {params}", "success": True}
    def get_tool_schema(self) -> dict:
        return {"name": self.name, "description": self.description, "parameters": {"type": "object", "properties": {"input": {"type": "string"}}}}
'''

_AGENT_SOURCE = '''
from app.core.plugin_base import AgentPlugin
class TestAgentPlugin(AgentPlugin):
    name = "test_agent"
    version = "2.0.0"
    description = "A test agent plugin"
    async def process(self, user_input: str, context: list | None = None) -> str:
        return f"test agent processed: {user_input}"
    async def process_stream(self, user_input: str, context: list | None = None):
        yield f"test agent stream: {user_input}"
'''

_WORKFLOW_SOURCE = '''
from app.core.plugin_base import WorkflowPlugin
class TestWorkflowPlugin(WorkflowPlugin):
    name = "test_workflow"
    version = "1.0.0"
    description = "A test workflow plugin"
    async def run(self, inputs: dict) -> dict:
        return {"workflow_result": inputs, "steps_completed": 3}
    def get_steps(self) -> list[dict]:
        return [{"name": "step1", "action": "analyze"}, {"name": "step2", "action": "transform"}, {"name": "step3", "action": "output"}]
'''


def _create_test_plugin(base_dir: str, name: str, ptype: str, source: str = "") -> str:
    pdir = os.path.join(base_dir, f"{ptype}s", name)
    os.makedirs(pdir, exist_ok=True)
    manifest = {
        "name": name,
        "version": "1.0.0",
        "description": f"Test {ptype} plugin",
        "author": "OpenPaper",
        "plugin_type": ptype,
        "entrypoint": "plugin.py",
        "dependencies": [],
        "permissions": [],
        "hooks": ["on_load"],
    }
    with open(os.path.join(pdir, "plugin.yaml"), "w") as f:
        yaml.dump(manifest, f)
    if source:
        with open(os.path.join(pdir, "plugin.py"), "w") as f:
            f.write(source)
    return pdir


@pytest.fixture
def plugin_dir():
    tmp = tempfile.mkdtemp()
    _create_test_plugin(tmp, "test_tool", "tool", _TOOL_SOURCE)
    _create_test_plugin(tmp, "test_agent", "agent", _AGENT_SOURCE)
    _create_test_plugin(tmp, "test_workflow", "workflow", _WORKFLOW_SOURCE)
    yield tmp
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def registry(plugin_dir):
    reg = PluginRegistry(base_dir=plugin_dir)
    set_plugin_registry(reg)
    yield reg
    set_plugin_registry(None)


class TestPluginSandbox:
    def test_check_permission_allowed(self):
        sandbox = PluginSandbox("test", [PluginPermission.MEMORY_READ, PluginPermission.TASK_READ])
        assert sandbox.check_permission(PluginPermission.MEMORY_READ) is True
        assert sandbox.check_permission(PluginPermission.TASK_READ) is True

    def test_check_permission_denied(self):
        sandbox = PluginSandbox("test", [PluginPermission.MEMORY_READ])
        assert sandbox.check_permission(PluginPermission.MEMORY_WRITE) is False
        assert sandbox.check_permission(PluginPermission.NETWORK) is False

    def test_require_permission_raises(self):
        sandbox = PluginSandbox("test", [])
        with pytest.raises(PermissionError):
            sandbox.require_permission(PluginPermission.AGENT_EXECUTE)

    def test_sanitize_path_allowed(self, plugin_dir):
        sandbox = PluginSandbox("test", [])
        path = sandbox.sanitize_path(os.path.join(plugin_dir, "test", "file.txt"))
        assert "test" in path

    def test_sanitize_path_escape(self):
        sandbox = PluginSandbox("test", [])
        with pytest.raises(PermissionError):
            sandbox.sanitize_path("../etc/passwd")


class TestPluginRegistry:
    def test_discover_returns_manifests(self, registry):
        manifests = registry.discover()
        names = [m.name for m in manifests]
        assert "test_tool" in names
        assert "test_agent" in names
        assert "test_workflow" in names

    def test_discover_and_load(self, registry):
        results = registry.discover_and_load()
        names = [r.name for r in results]
        assert "test_tool" in names
        assert "test_agent" in names
        assert "test_workflow" in names
        assert all(r.status in (PluginStatus.LOADED, PluginStatus.ENABLED, PluginStatus.ERROR) for r in results)

    def test_list_plugins(self, registry):
        registry.discover_and_load()
        plugins = registry.list_plugins()
        assert len(plugins) >= 3

    def test_list_plugins_by_type(self, registry):
        registry.discover_and_load()
        tools = registry.list_plugins(plugin_type=PluginType.TOOL)
        assert len(tools) >= 1
        assert all(p.plugin_type == PluginType.TOOL for p in tools)

    def test_get_plugin(self, registry):
        registry.discover_and_load()
        plugin = registry.get_plugin("test_tool")
        assert plugin is not None
        assert plugin.name == "test_tool"

    def test_enable_plugin(self, registry):
        registry.discover_and_load()
        result = registry.enable("test_tool")
        assert result.status == PluginStatus.ENABLED
        assert registry.get_status("test_tool") == PluginStatus.ENABLED

    def test_disable_plugin(self, registry):
        registry.discover_and_load()
        registry.enable("test_tool")
        result = registry.disable("test_tool")
        assert result.status == PluginStatus.DISABLED

    def test_unload_plugin(self, registry):
        registry.discover_and_load()
        assert registry.unload("test_tool") is True
        assert registry.get_plugin("test_tool") is None
        assert registry.unload("nonexistent") is False

    def test_remove_plugin(self, registry):
        registry.discover_and_load()
        assert registry.remove("test_tool") is True
        assert registry.get_plugin("test_tool") is None

    def test_hot_reload(self, registry):
        registry.discover_and_load()
        registry.enable("test_tool")
        result = registry.hot_reload("test_tool")
        assert result is not None
        assert result.name == "test_tool"

    def test_count(self, registry):
        assert registry.count() == 0
        registry.discover_and_load()
        assert registry.count() >= 3

    def test_get_sandbox(self, registry):
        registry.discover_and_load()
        sandbox = registry.get_sandbox("test_agent")
        assert sandbox is not None
        assert sandbox.check_permission(PluginPermission.NETWORK) is False


class TestPluginBaseClasses:
    def test_tool_plugin_execute(self, registry):
        registry.discover_and_load()
        plugin = registry.get_plugin("test_tool")
        assert plugin is not None
        import asyncio
        result = asyncio.run(plugin.execute({"input": "hello"}))
        assert result["success"] is True

    def test_tool_plugin_schema(self, registry):
        registry.discover_and_load()
        plugin = registry.get_plugin("test_tool")
        assert plugin is not None
        schema = plugin.get_tool_schema()
        assert schema["name"] == "test_tool"

    def test_agent_plugin_process(self, registry):
        registry.discover_and_load()
        plugin = registry.get_plugin("test_agent")
        assert plugin is not None
        import asyncio
        result = asyncio.run(plugin.process("hello"))
        assert "test agent" in result

    def test_workflow_plugin_run(self, registry):
        registry.discover_and_load()
        plugin = registry.get_plugin("test_workflow")
        assert plugin is not None
        import asyncio
        result = asyncio.run(plugin.run({"data": "test"}))
        assert result["steps_completed"] == 3

    def test_workflow_plugin_steps(self, registry):
        registry.discover_and_load()
        plugin = registry.get_plugin("test_workflow")
        assert plugin is not None
        steps = plugin.get_steps()
        assert len(steps) == 3


class TestPluginManifest:
    def test_manifest_creation(self):
        manifest = PluginManifest(
            name="test", version="1.0.0", description="test plugin", plugin_type=PluginType.TOOL,
        )
        assert manifest.name == "test"
        assert manifest.plugin_type == PluginType.TOOL
        assert manifest.version == "1.0.0"

    def test_manifest_with_all_fields(self):
        manifest = PluginManifest(
            name="full", version="2.0.0", description="full plugin", author="me",
            plugin_type=PluginType.PROVIDER, entrypoint="main.py",
            dependencies=["httpx>=0.27"],
            permissions=[PluginPermission.MEMORY_READ, PluginPermission.BUS_PUBLISH],
            hooks=["on_load", "on_task_created"],
            config_schema={"api_key": {"type": "string"}},
        )
        assert len(manifest.permissions) == 2
        assert len(manifest.hooks) == 2
        assert manifest.entrypoint == "main.py"

    def test_plugin_create_schema(self):
        create = PluginCreate(
            name="new_plugin", description="new", plugin_type=PluginType.WORKFLOW, source="print('hello')",
        )
        assert create.name == "new_plugin"
        assert create.source == "print('hello')"

    def test_plugin_response_schema(self):
        resp = PluginResponse(
            id="p-1", name="test", version="1.0.0", description="test", author="",
            plugin_type=PluginType.TOOL, status=PluginStatus.ENABLED,
        )
        assert resp.id == "p-1"
        assert resp.status == PluginStatus.ENABLED


class TestPluginTypes:
    def test_all_plugin_types(self):
        types = [e.value for e in PluginType]
        assert "provider" in types
        assert "agent" in types
        assert "tool" in types
        assert "workflow" in types
        assert "ui" in types

    def test_all_plugin_hooks(self):
        hooks = [e.value for e in PluginHook]
        assert "on_load" in hooks
        assert "on_unload" in hooks
        assert "on_agent_start" in hooks
        assert "on_agent_stop" in hooks
        assert "on_task_created" in hooks
        assert "on_task_completed" in hooks
        assert "on_message_received" in hooks

    def test_all_permissions(self):
        perms = [p.value for p in PluginPermission]
        assert "memory:read" in perms
        assert "memory:write" in perms
        assert "agent:execute" in perms
        assert "network" in perms
        assert "system:config" in perms
