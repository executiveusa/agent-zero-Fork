"""Spec-Driven Development Workflow (Zenflow Pattern)

Enforces structured 4-phase development:
Plan → Implement → Test → Review

Prevents "vibe coding" by requiring technical specifications BEFORE code.
Each phase has gates that must pass before proceeding.

Actions
-------
execute_workflow  - Run full 4-phase workflow for a task
get_phase_status  - Check status of workflow phases
approve_phase     - Manually approve a phase (override)
reject_phase      - Reject a phase and provide feedback

Environment
-----------
SPEC_WORKFLOW_ENABLED    - Enable spec-driven workflow (default: true)
SPEC_WORKFLOW_STRICT     - Enforce phase gates strictly (default: true)
PLANNING_MODEL           - Model for spec generation (default: claude-opus-4-5)
REVIEW_MODEL             - Model for committee review (default: auto)
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class Phase(Enum):
    PLAN = "plan"
    IMPLEMENT = "implement"
    TEST = "test"
    REVIEW = "review"


class PhaseStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class PhaseResult:
    phase: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    model_used: Optional[str]
    output: Optional[Dict]
    issues: List[str]
    approval_required: bool
    approved: bool


@dataclass
class WorkflowState:
    workflow_id: str
    task_description: str
    created_at: str
    phases: Dict[str, PhaseResult]
    current_phase: str
    completed: bool
    success: bool


class SpecWorkflow:
    def __init__(self, workspace_path: str = ".") -> None:
        self.workspace = Path(workspace_path)
        self.workflows_dir = self.workspace / ".workflows"
        self.workflows_dir.mkdir(exist_ok=True)

        self.enabled = os.getenv("SPEC_WORKFLOW_ENABLED", "true").lower() == "true"
        self.strict = os.getenv("SPEC_WORKFLOW_STRICT", "true").lower() == "true"
        self.planning_model = os.getenv("PLANNING_MODEL", "claude-opus-4-5")
        self.review_model = os.getenv("REVIEW_MODEL", "auto")

    def _get_workflow_path(self, workflow_id: str) -> Path:
        return self.workflows_dir / f"{workflow_id}.json"

    def _save_workflow(self, state: WorkflowState) -> None:
        with open(self._get_workflow_path(state.workflow_id), "w") as f:
            json.dump(asdict(state), f, indent=2)

    def _load_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        path = self._get_workflow_path(workflow_id)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
            # Convert dict back to WorkflowState
            phases = {
                k: PhaseResult(**v) for k, v in data["phases"].items()
            }
            data["phases"] = phases
            return WorkflowState(**data)

    def execute_workflow(
        self,
        task_description: str,
        workflow_id: Optional[str] = None
    ) -> dict:
        """
        Execute full 4-phase spec-driven workflow

        Returns workflow state with each phase's results
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Spec workflow is disabled. Set SPEC_WORKFLOW_ENABLED=true"
            }

        # Create or load workflow
        if workflow_id:
            state = self._load_workflow(workflow_id)
            if not state:
                return {"success": False, "error": f"Workflow {workflow_id} not found"}
        else:
            workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            state = WorkflowState(
                workflow_id=workflow_id,
                task_description=task_description,
                created_at=datetime.now().isoformat(),
                phases={
                    Phase.PLAN.value: PhaseResult(
                        phase=Phase.PLAN.value,
                        status=PhaseStatus.PENDING.value,
                        started_at=None,
                        completed_at=None,
                        model_used=None,
                        output=None,
                        issues=[],
                        approval_required=True,
                        approved=False
                    ),
                    Phase.IMPLEMENT.value: PhaseResult(
                        phase=Phase.IMPLEMENT.value,
                        status=PhaseStatus.BLOCKED.value,
                        started_at=None,
                        completed_at=None,
                        model_used=None,
                        output=None,
                        issues=[],
                        approval_required=False,
                        approved=False
                    ),
                    Phase.TEST.value: PhaseResult(
                        phase=Phase.TEST.value,
                        status=PhaseStatus.BLOCKED.value,
                        started_at=None,
                        completed_at=None,
                        model_used=None,
                        output=None,
                        issues=[],
                        approval_required=False,
                        approved=False
                    ),
                    Phase.REVIEW.value: PhaseResult(
                        phase=Phase.REVIEW.value,
                        status=PhaseStatus.BLOCKED.value,
                        started_at=None,
                        completed_at=None,
                        model_used=None,
                        output=None,
                        issues=[],
                        approval_required=True,
                        approved=False
                    ),
                },
                current_phase=Phase.PLAN.value,
                completed=False,
                success=False
            )

        # Execute phases sequentially
        phase_order = [Phase.PLAN, Phase.IMPLEMENT, Phase.TEST, Phase.REVIEW]

        for phase in phase_order:
            phase_key = phase.value
            phase_result = state.phases[phase_key]

            # Skip if already completed
            if phase_result.status == PhaseStatus.COMPLETED.value:
                continue

            # Check if blocked by previous phase
            if phase != Phase.PLAN:
                prev_phase = phase_order[phase_order.index(phase) - 1].value
                prev_result = state.phases[prev_phase]
                if prev_result.status != PhaseStatus.COMPLETED.value:
                    phase_result.status = PhaseStatus.BLOCKED.value
                    phase_result.issues.append(
                        f"Blocked: Previous phase '{prev_phase}' not completed"
                    )
                    continue

            # Execute phase
            state.current_phase = phase_key
            phase_result.status = PhaseStatus.IN_PROGRESS.value
            phase_result.started_at = datetime.now().isoformat()

            # Save state
            self._save_workflow(state)

            # Generate phase instructions for agent
            if phase == Phase.PLAN:
                instructions = self._generate_plan_instructions(task_description)
            elif phase == Phase.IMPLEMENT:
                spec = state.phases[Phase.PLAN.value].output
                instructions = self._generate_implement_instructions(spec)
            elif phase == Phase.TEST:
                code = state.phases[Phase.IMPLEMENT.value].output
                instructions = self._generate_test_instructions(code)
            elif phase == Phase.REVIEW:
                code = state.phases[Phase.IMPLEMENT.value].output
                spec = state.phases[Phase.PLAN.value].output
                instructions = self._generate_review_instructions(code, spec)

            # Return instructions for agent to execute
            # (Actual execution happens via parallel_delegate or direct agent call)
            return {
                "success": True,
                "workflow_id": workflow_id,
                "current_phase": phase_key,
                "phase_status": "awaiting_execution",
                "instructions": instructions,
                "next_action": f"Execute {phase_key} phase, then call complete_phase",
                "message": f"Workflow {workflow_id} ready for {phase_key} phase"
            }

        # All phases completed
        state.completed = True
        state.success = all(
            p.status == PhaseStatus.COMPLETED.value
            for p in state.phases.values()
        )
        self._save_workflow(state)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "completed": True,
            "all_phases_passed": state.success,
            "phases": {k: asdict(v) for k, v in state.phases.items()}
        }

    def _generate_plan_instructions(self, task_description: str) -> dict:
        return {
            "phase": "PLAN",
            "model": self.planning_model,
            "task": "Generate technical specification",
            "prompt": f"""Generate a detailed technical specification for the following task:

TASK:
{task_description}

Your specification MUST include:

1. **Overview**
   - What are we building?
   - Why is it needed?
   - Success criteria

2. **Architecture**
   - Components/modules
   - Data flow
   - External dependencies

3. **API/Interface Design**
   - Public functions/endpoints
   - Input/output formats
   - Error handling

4. **Data Models**
   - Schemas/structures
   - Validation rules
   - Relationships

5. **Security Considerations**
   - Authentication/authorization
   - Input validation
   - Data protection

6. **Testing Strategy**
   - Unit test coverage
   - Integration tests
   - Edge cases

7. **Implementation Plan**
   - Step-by-step breakdown
   - Time estimates
   - Dependencies

Output as structured Markdown with clear sections.
""",
            "success_criteria": [
                "All 7 sections present",
                "Specific (not vague)",
                "Testable/measurable",
                "Addresses security",
                "Includes edge cases"
            ]
        }

    def _generate_implement_instructions(self, spec: Optional[Dict]) -> dict:
        spec_text = spec.get("content", "") if spec else "No spec available"
        return {
            "phase": "IMPLEMENT",
            "model": "gemini-2.0-flash",  # Fast coding model
            "task": "Implement code according to specification",
            "prompt": f"""Implement the following specification EXACTLY:

SPECIFICATION:
{spec_text}

REQUIREMENTS:
- Follow the spec precisely (no deviations)
- Include all security measures from spec
- Add docstrings for public functions
- Handle all edge cases mentioned in spec
- Write code that matches the testing strategy

DO NOT:
- Add features not in spec
- Skip security considerations
- Ignore edge cases
- Write untestable code

Output: Complete, production-ready code with tests.
""",
            "success_criteria": [
                "Matches spec exactly",
                "All public functions documented",
                "Includes tests",
                "Handles edge cases",
                "Security measures implemented"
            ]
        }

    def _generate_test_instructions(self, code: Optional[Dict]) -> dict:
        code_content = code.get("content", "") if code else "No code available"
        return {
            "phase": "TEST",
            "model": "gpt-4-turbo",  # Good at test generation
            "task": "Run tests and verify functionality",
            "prompt": f"""Test the following code thoroughly:

CODE:
{code_content}

TESTING REQUIREMENTS:
1. Run all unit tests
2. Run integration tests
3. Check code coverage (target: ≥70%)
4. Test edge cases explicitly
5. Run linter/formatter
6. Check for security issues

Output: Test results with pass/fail for each test, coverage percentage, and any issues found.
""",
            "success_criteria": [
                "All tests pass",
                "Coverage ≥70%",
                "Linter clean",
                "No security issues"
            ]
        }

    def _generate_review_instructions(
        self,
        code: Optional[Dict],
        spec: Optional[Dict]
    ) -> dict:
        code_content = code.get("content", "") if code else "No code available"
        spec_content = spec.get("content", "") if spec else "No spec available"

        return {
            "phase": "REVIEW",
            "model": self.review_model,
            "task": "Committee review (multi-model verification)",
            "prompt": f"""Conduct a thorough committee review of this implementation:

ORIGINAL SPECIFICATION:
{spec_content}

IMPLEMENTATION:
{code_content}

REVIEW CHECKLIST:
1. **Spec Compliance** - Does code match spec exactly?
2. **Code Quality** - Clean, maintainable, well-structured?
3. **Security** - All security measures implemented?
4. **Performance** - No obvious bottlenecks?
5. **Testing** - Adequate test coverage?
6. **Documentation** - Clear docstrings and comments?
7. **Edge Cases** - All handled properly?

Use committee review tool with opposing model to catch blind spots.

Output: JSON with approval/rejection and detailed feedback.
""",
            "success_criteria": [
                "Committee approves",
                "No critical issues",
                "Code matches spec",
                "Security verified",
                "Performance acceptable"
            ]
        }

    def complete_phase(
        self,
        workflow_id: str,
        phase: str,
        result: Dict,
        approved: bool = False
    ) -> dict:
        """Mark a phase as complete with results"""
        state = self._load_workflow(workflow_id)
        if not state:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}

        if phase not in state.phases:
            return {"success": False, "error": f"Invalid phase: {phase}"}

        phase_result = state.phases[phase]
        phase_result.status = PhaseStatus.COMPLETED.value if approved else PhaseStatus.FAILED.value
        phase_result.completed_at = datetime.now().isoformat()
        phase_result.output = result
        phase_result.approved = approved

        # Unblock next phase if approved
        if approved:
            phase_order = [Phase.PLAN.value, Phase.IMPLEMENT.value, Phase.TEST.value, Phase.REVIEW.value]
            current_idx = phase_order.index(phase)
            if current_idx < len(phase_order) - 1:
                next_phase = phase_order[current_idx + 1]
                state.phases[next_phase].status = PhaseStatus.PENDING.value

        self._save_workflow(state)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "phase": phase,
            "status": phase_result.status,
            "approved": approved
        }

    def get_phase_status(self, workflow_id: str) -> dict:
        """Get status of all phases in workflow"""
        state = self._load_workflow(workflow_id)
        if not state:
            return {"success": False, "error": f"Workflow {workflow_id} not found"}

        return {
            "success": True,
            "workflow_id": workflow_id,
            "current_phase": state.current_phase,
            "completed": state.completed,
            "phases": {k: asdict(v) for k, v in state.phases.items()}
        }


def process_tool(tool_input: dict) -> dict:
    """Process spec workflow actions"""
    workspace = tool_input.get("workspace_path", ".")
    workflow = SpecWorkflow(workspace)

    action = tool_input.get("action", "")

    try:
        if action == "execute_workflow":
            return workflow.execute_workflow(
                task_description=tool_input["task_description"],
                workflow_id=tool_input.get("workflow_id")
            )

        elif action == "complete_phase":
            return workflow.complete_phase(
                workflow_id=tool_input["workflow_id"],
                phase=tool_input["phase"],
                result=tool_input.get("result", {}),
                approved=tool_input.get("approved", False)
            )

        elif action == "get_phase_status":
            return workflow.get_phase_status(
                workflow_id=tool_input["workflow_id"]
            )

        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "execute_workflow",
                    "complete_phase",
                    "get_phase_status"
                ]
            }

    except Exception as e:
        return {"success": False, "error": str(e)}
