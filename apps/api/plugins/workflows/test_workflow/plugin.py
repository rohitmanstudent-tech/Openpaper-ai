"""Test workflow plugin for unit testing."""

from app.core.plugin_base import WorkflowPlugin


class TestWorkflowPlugin(WorkflowPlugin):
    name = "test_workflow"
    version = "1.0.0"
    description = "A test workflow plugin"

    async def run(self, inputs: dict) -> dict:
        return {"workflow_result": inputs, "steps_completed": 3}

    def get_steps(self) -> list[dict]:
        return [
            {"name": "step1", "action": "analyze"},
            {"name": "step2", "action": "transform"},
            {"name": "step3", "action": "output"},
        ]
