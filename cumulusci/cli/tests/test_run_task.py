"""Tests for the RunTaskCommand class"""

from cumulusci.cli.cci import RunTaskCommand
import click
import pytest
from unittest.mock import Mock, patch

from cumulusci.cli import cci
from cumulusci.core.config import TaskConfig
from cumulusci.core.config import BaseProjectConfig
from cumulusci.core.exceptions import CumulusCIUsageError, CumulusCIException
from cumulusci.cli.tests.utils import run_click_command, DummyTask


@pytest.fixture
def runtime():
    runtime = Mock()
    runtime.get_org.return_value = (None, None)
    runtime.project_config = BaseProjectConfig(
        None,
        config={
            "tasks": {
                "dummy-task": {"class_path": "cumulusci.cli.tests.utils.DummyTask"},
                "lots-o-options-task": {
                    "class_path": "cumulusci.cli.tests.utils.MultipleOptionsTask"
                },
                "dummy-derived-task": {
                    "class_path": "cumulusci.cli.tests.test_run_task.DummyDerivedTask"
                },
            }
        },
    )
    return runtime


def test_task_run(runtime):
    DummyTask._run_task = Mock()
    multi_cmd = cci.RunTaskCommand()
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        cmd = multi_cmd.get_command(Mock(), "dummy-task")
        run_click_command(cmd, "dummy-task", color="blue", runtime=runtime)

    DummyTask._run_task.assert_called_once()


def test_task_run__debug_before(runtime):
    DummyTask._run_task = Mock()
    multi_cmd = cci.RunTaskCommand()

    set_trace = Mock(side_effect=SetTrace)
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        with patch("pdb.set_trace", set_trace):
            with pytest.raises(SetTrace):
                cmd = multi_cmd.get_command(Mock(), "dummy-task")
                run_click_command(
                    cmd,
                    "dummy_task",
                    color="blue",
                    debug_before=True,
                    debug_after=False,
                    runtime=runtime,
                )


def test_task_run__debug_after(runtime):
    DummyTask._run_task = Mock()
    multi_cmd = cci.RunTaskCommand()

    set_trace = Mock(side_effect=SetTrace)
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        with patch("pdb.set_trace", set_trace):
            with pytest.raises(SetTrace):
                cmd = multi_cmd.get_command(Mock(), "dummy-task")
                run_click_command(
                    cmd,
                    "dummy-task",
                    color="blue",
                    debug_before=False,
                    debug_after=True,
                    runtime=runtime,
                )


def test_task_run__list_commands(runtime):
    multi_cmd = cci.RunTaskCommand()
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        commands = multi_cmd.list_commands(Mock())
    assert commands == ["dummy-derived-task", "dummy-task", "lots-o-options-task"]


def test_task_run__resolve_command(runtime):
    args = ["dummy-task", "-o", "color", "blue"]
    multi_cmd = cci.RunTaskCommand()
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        cmd_name, cmd, args = multi_cmd.resolve_command(Mock(), args)

    assert cmd_name == "dummy-task"
    assert isinstance(cmd, click.Command)
    assert args == [
        "--color",
        "blue",
    ]


def test_convert_old_option_syntax__nothing_to_convert():
    args = ["test-task", "run", "util_sleep", "--seconds", "3.88"]
    converted = RunTaskCommand()._convert_old_option_syntax(args)
    assert args == converted


def test_convert_old_option_syntax__convert_single_option(runtime):
    args = ["dummy-task", "-o", "color", "blue"]
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        converted = RunTaskCommand()._convert_old_option_syntax(args)
    assert converted == ["dummy-task", "--color", "blue"]


def test_convert_old_option_syntax__convert_multiple_options(runtime):
    args = [
        "lots-o-options-task",
        "-o",
        "foo",
        "fooey",
        "-o",
        "bar",
        "bary",
        "-o",
        "baz",
        "bazzy",
    ]
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        converted = RunTaskCommand()._convert_old_option_syntax(args)
    assert converted == [
        "lots-o-options-task",
        "--foo",
        "fooey",
        "--bar",
        "bary",
        "--baz",
        "bazzy",
    ]


def test_convert_old_option_syntax__convert_mixed_options(runtime):
    args = [
        "lots-o-options-task",
        "-o",
        "foo",
        "fooey",
        "--bar",
        "bary",
        "-o",
        "baz",
        "bazzy",
    ]
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        converted = RunTaskCommand()._convert_old_option_syntax(args)
    assert converted == [
        "lots-o-options-task",
        "--foo",
        "fooey",
        "--bar",
        "bary",
        "--baz",
        "bazzy",
    ]


def test_convert_old_option_syntax__duplicate_option(runtime):
    """We only test duplicate options specified in the old
    option syntax: -o name value. Click takes care of the new
    syntax for us."""
    args = [
        "lots-o-options-task",
        "-o",
        "foo",
        "fooey",
        "--bar",
        "bary",
        "-o",
        "baz",
        "bazzy",
        "-o",
        "foo",
        "duplicate",
    ]
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        with pytest.raises(CumulusCIUsageError):
            RunTaskCommand()._convert_old_option_syntax(args)


def test_option_in_task__true(runtime):
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        assert RunTaskCommand()._option_in_task("color", "dummy-task")


def test_option_in_task__false(runtime):
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        assert not RunTaskCommand()._option_in_task("pizza", "dummy-task")


def test_option_in_task__option_in_base_class(runtime):
    with patch("cumulusci.cli.cci.RUNTIME", runtime):
        assert RunTaskCommand()._option_in_task("color", "dummy-derived-task")


def test_get_task_options_in_hierarchy__fail_to_import(runtime):
    t_config = TaskConfig(
        config={"class_path": "cumulusci.cli.tests.test_run_task.DoesNotExistTask"}
    )
    with pytest.raises(CumulusCIException):
        RunTaskCommand()._get_task_options_in_hierarchy(t_config)


def test_get_task_options_in_hierarchy__options_found(runtime):
    t_config = TaskConfig(
        config={"class_path": "cumulusci.cli.tests.test_run_task.DummyDerivedTask"}
    )
    options = RunTaskCommand()._get_task_options_in_hierarchy(t_config)
    assert options == ["color"]


class SetTrace(Exception):
    pass


class DummyDerivedTask(DummyTask):
    def _run_task(self):
        click.echo(f"<{self.__class__}>\n\tcolor: {self.options['color']}")