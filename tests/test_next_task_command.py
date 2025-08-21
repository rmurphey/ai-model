"""
Comprehensive tests for the NextTaskAnalyzer command module.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

from src.commands.next_task import NextTaskAnalyzer, Task


class TestTask:
    """Test the Task dataclass"""
    
    def test_task_creation(self):
        """Test creating a Task object"""
        task = Task(
            title="Fix tests",
            description="Tests are failing",
            priority=100,
            category="critical",
            action="pytest",
            reasoning="Tests must pass",
            metadata={"count": 5}
        )
        
        assert task.title == "Fix tests"
        assert task.priority == 100
        assert task.category == "critical"
        assert task.metadata["count"] == 5
    
    def test_task_defaults(self):
        """Test Task with default metadata"""
        task = Task(
            title="Review",
            description="Code review",
            priority=50,
            category="medium",
            action="review",
            reasoning="Quality"
        )
        
        assert task.metadata == {}


class TestNextTaskAnalyzer:
    """Test the NextTaskAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create analyzer with temp directory"""
        return NextTaskAnalyzer(str(tmp_path))
    
    def test_analyzer_initialization(self, tmp_path):
        """Test analyzer initialization"""
        analyzer = NextTaskAnalyzer(str(tmp_path))
        assert analyzer.repo_path == tmp_path
        assert analyzer.tasks == []
    
    def test_run_command_success(self, analyzer):
        """Test successful command execution"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="output",
                stderr=""
            )
            
            code, stdout, stderr = analyzer.run_command(['echo', 'test'])
            
            assert code == 0
            assert stdout == "output"
            assert stderr == ""
    
    def test_run_command_failure(self, analyzer):
        """Test failed command execution"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="error"
            )
            
            code, stdout, stderr = analyzer.run_command(['false'])
            
            assert code == 1
            assert stderr == "error"
    
    def test_run_command_timeout(self, analyzer):
        """Test command timeout"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired('cmd', 10)
            
            code, stdout, stderr = analyzer.run_command(['sleep', '100'])
            
            assert code == -1
            assert stderr == "Command timed out"
    
    def test_check_git_status_with_changes(self, analyzer):
        """Test git status check with uncommitted changes"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.return_value = (0, " M file1.py\n M file2.py\n?? new.py", "")
            
            analyzer.check_git_status()
            
            assert len(analyzer.tasks) == 2
            assert analyzer.tasks[0].title == "Commit uncommitted changes"
            assert analyzer.tasks[0].priority == 75
            assert analyzer.tasks[1].title == "Review untracked files"
    
    def test_check_git_status_clean(self, analyzer):
        """Test git status check with clean repo"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.return_value = (0, "", "")
            
            analyzer.check_git_status()
            
            assert len(analyzer.tasks) == 0
    
    def test_check_unpushed_commits(self, analyzer):
        """Test checking for unpushed commits"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.side_effect = [
                (0, "main", ""),  # Current branch
                (0, "5", ""),  # Commits ahead
                (0, "commit1\ncommit2", "")  # Commit messages
            ]
            
            analyzer.check_unpushed_commits()
            
            assert len(analyzer.tasks) == 1
            assert analyzer.tasks[0].title == "Push commits to remote"
            assert analyzer.tasks[0].priority == 70
            assert "5 unpushed commit(s)" in analyzer.tasks[0].description
    
    def test_check_unpushed_commits_none(self, analyzer):
        """Test when no unpushed commits"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.side_effect = [
                (0, "main", ""),
                (0, "0", "")
            ]
            
            analyzer.check_unpushed_commits()
            
            assert len(analyzer.tasks) == 0
    
    def test_check_github_issues(self, analyzer):
        """Test checking GitHub issues"""
        issues = [
            {
                "number": 1,
                "title": "Bug fix",
                "labels": [{"name": "bug"}]
            }
        ]
        
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.return_value = (0, json.dumps(issues), "")
            
            analyzer.check_github_issues()
            
            assert len(analyzer.tasks) == 1
            assert "issue #1" in analyzer.tasks[0].title
            assert analyzer.tasks[0].priority == 65  # High priority for bug
    
    def test_check_github_issues_none(self, analyzer):
        """Test when no GitHub issues"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.return_value = (0, "[]", "")
            
            analyzer.check_github_issues()
            
            assert len(analyzer.tasks) == 0
    
    def test_check_pull_requests(self, analyzer):
        """Test checking pull requests"""
        prs = [
            {
                "number": 42,
                "title": "Add feature",
                "author": {"login": "user"}
            }
        ]
        
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.return_value = (0, json.dumps(prs), "")
            
            analyzer.check_pull_requests()
            
            assert len(analyzer.tasks) == 1
            assert "PR #42" in analyzer.tasks[0].title
            assert analyzer.tasks[0].priority == 60
    
    def test_check_test_status_passing(self, analyzer):
        """Test when all tests pass"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.side_effect = [
                (0, "", ""),  # Collection success
                (0, "All tests passed", "")  # Tests pass
            ]
            
            analyzer.check_test_status()
            
            assert len(analyzer.tasks) == 0
    
    def test_check_test_status_failing(self, analyzer):
        """Test when tests are failing"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.side_effect = [
                (0, "", ""),  # Collection success
                (1, "FAILED test_foo.py::test_bar - AssertionError", "")  # Tests fail
            ]
            
            analyzer.check_test_status()
            
            assert len(analyzer.tasks) == 1
            assert analyzer.tasks[0].title == "Fix failing tests"
            assert analyzer.tasks[0].priority == 100
            assert analyzer.tasks[0].category == "critical"
    
    def test_check_todo_comments(self, analyzer):
        """Test finding TODO comments"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.return_value = (
                0,
                "src/file.py:10:# TODO: Fix this\nsrc/other.py:20:# FIXME: Bug here",
                ""
            )
            
            analyzer.check_todo_comments()
            
            assert len(analyzer.tasks) == 1
            assert "2 TODO comment(s)" in analyzer.tasks[0].title
            assert analyzer.tasks[0].priority == 50
    
    def test_check_todo_comments_none(self, analyzer):
        """Test when no TODO comments"""
        with patch.object(analyzer, 'run_command') as mock_run:
            mock_run.return_value = (1, "", "")
            
            analyzer.check_todo_comments()
            
            assert len(analyzer.tasks) == 0
    
    def test_check_documentation(self, analyzer):
        """Test documentation staleness check"""
        with patch.object(analyzer, 'run_command') as mock_run:
            # README last updated 10 days ago
            readme_time = str(int((datetime.now() - timedelta(days=10)).timestamp()))
            # Code updated yesterday
            code_time = str(int((datetime.now() - timedelta(days=1)).timestamp()))
            
            mock_run.side_effect = [
                (0, readme_time, ""),
                (0, code_time, "")
            ]
            
            analyzer.check_documentation()
            
            assert len(analyzer.tasks) == 1
            assert "Update README" in analyzer.tasks[0].title
            assert analyzer.tasks[0].priority == 25
    
    def test_analyze_full_workflow(self, analyzer):
        """Test full analysis workflow"""
        # Mock all check methods to add tasks
        with patch.object(analyzer, 'check_test_status') as mock_test:
            with patch.object(analyzer, 'check_git_status') as mock_git:
                with patch.object(analyzer, 'check_unpushed_commits') as mock_unpushed:
                    with patch.object(analyzer, 'check_github_issues'):
                        with patch.object(analyzer, 'check_pull_requests'):
                            with patch.object(analyzer, 'check_todo_comments'):
                                with patch.object(analyzer, 'check_documentation'):
                                    # Configure mocks to add tasks
                                    def add_high_task():
                                        analyzer.tasks.append(Task("High", "High priority", 80, "high", "act", "reason"))
                                    def add_low_task():
                                        analyzer.tasks.append(Task("Low", "Low priority", 20, "low", "act", "reason"))
                                    def add_med_task():
                                        analyzer.tasks.append(Task("Med", "Medium priority", 50, "medium", "act", "reason"))
                                    
                                    mock_test.side_effect = add_high_task
                                    mock_git.side_effect = add_med_task
                                    mock_unpushed.side_effect = add_low_task
                                    
                                    tasks = analyzer.analyze()
                                    
                                    # Should be sorted by priority
                                    assert len(tasks) == 3
                                    assert tasks[0].priority == 80
                                    assert tasks[1].priority == 50
                                    assert tasks[2].priority == 20
    
    def test_format_output_no_tasks(self, analyzer):
        """Test output formatting with no tasks"""
        output = analyzer.format_output([])
        
        assert "✅ All clear!" in output
        assert "Consider:" in output
    
    def test_format_output_with_tasks(self, analyzer):
        """Test output formatting with tasks"""
        tasks = [
            Task(
                title="Fix critical bug",
                description="System is down",
                priority=100,
                category="critical",
                action="debug now",
                reasoning="Production issue",
                metadata={"severity": "high"}
            ),
            Task(
                title="Review PR",
                description="Needs review",
                priority=60,
                category="medium",
                action="gh pr view",
                reasoning="Blocking team"
            )
        ]
        
        output = analyzer.format_output(tasks, verbose=False)
        
        assert "NEXT PRIORITY TASK" in output
        assert "Fix critical bug" in output
        assert "🔴 CRITICAL" in output
        assert "OTHER TASKS" in output
        assert "Review PR" in output
    
    def test_format_output_verbose(self, analyzer):
        """Test verbose output formatting"""
        tasks = [
            Task(
                title="Task",
                description="Description",
                priority=50,
                category="medium",
                action="action",
                reasoning="reason",
                metadata={"files": ["file1.py", "file2.py"]}
            )
        ]
        
        output = analyzer.format_output(tasks, verbose=True)
        
        assert "Details:" in output
        assert "file1.py" in output
    
    def test_format_priority(self, analyzer):
        """Test priority formatting"""
        assert "🔴 CRITICAL" in analyzer._format_priority(100, "critical")
        assert "🟠 HIGH" in analyzer._format_priority(75, "high")
        assert "🟡 MEDIUM" in analyzer._format_priority(50, "medium")
        assert "🟢 LOW" in analyzer._format_priority(25, "low")
    
    def test_get_quick_stats(self, analyzer):
        """Test quick stats generation"""
        tasks = [
            Task("Fix tests", "Tests failing", 100, "critical", "pytest", "reason"),
            Task("Commit uncommitted changes", "Uncommitted", 75, "high", "git commit", "reason"),
            Task("Work on issue", "Open issue", 40, "medium", "gh issue", "reason"),
            Task("TODO", "TODO found", 50, "medium", "grep", "reason")
        ]
        
        stats = analyzer._get_quick_stats(tasks)
        
        assert any("Tests failing" in s for s in stats)
        assert any("uncommitted" in s for s in stats)
        assert any("open issue" in s for s in stats)
        assert any("TODO" in s for s in stats)


class TestNextTaskIntegration:
    """Integration tests for next task command"""
    
    def test_main_function_json_output(self):
        """Test main function with JSON output"""
        with patch('sys.argv', ['next_task.py', '--json']):
            with patch('src.commands.next_task.NextTaskAnalyzer') as mock_analyzer:
                mock_instance = mock_analyzer.return_value
                mock_instance.analyze.return_value = [
                    Task("Test", "Desc", 50, "medium", "action", "reason")
                ]
                
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit'):
                        from src.commands.next_task import main
                        main()
                
                # Should print JSON
                call_args = mock_print.call_args[0][0]
                parsed = json.loads(call_args)
                assert parsed['tasks'][0]['title'] == "Test"
    
    def test_main_function_verbose(self):
        """Test main function with verbose flag"""
        with patch('sys.argv', ['next_task.py', '-v']):
            with patch('src.commands.next_task.NextTaskAnalyzer') as mock_analyzer:
                mock_instance = mock_analyzer.return_value
                mock_instance.analyze.return_value = []
                mock_instance.format_output.return_value = "Verbose output"
                
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit'):
                        from src.commands.next_task import main
                        main()
                
                mock_instance.format_output.assert_called_with([], verbose=True)
    
    def test_main_function_all_tasks(self):
        """Test main function with --all flag"""
        with patch('sys.argv', ['next_task.py', '--all']):
            with patch('src.commands.next_task.NextTaskAnalyzer') as mock_analyzer:
                mock_instance = mock_analyzer.return_value
                mock_instance.analyze.return_value = [
                    Task("T1", "D1", 80, "high", "a1", "r1", {"k": "v"}),
                    Task("T2", "D2", 40, "medium", "a2", "r2")
                ]
                
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit'):
                        from src.commands.next_task import main
                        main()
                
                # Should print all task details
                output = str(mock_print.call_args_list)
                assert "T1" in output
                assert "T2" in output
                assert "Metadata" in output
    
    def test_exit_code_critical(self):
        """Test exit code when critical task exists"""
        with patch('sys.argv', ['next_task.py']):
            with patch('src.commands.next_task.NextTaskAnalyzer') as mock_analyzer:
                mock_instance = mock_analyzer.return_value
                mock_instance.analyze.return_value = [
                    Task("Critical", "Desc", 100, "critical", "action", "reason")
                ]
                mock_instance.format_output.return_value = "output"
                
                with patch('builtins.print'):
                    with pytest.raises(SystemExit) as exc_info:
                        from src.commands.next_task import main
                        main()
                
                assert exc_info.value.code == 1
    
    def test_exit_code_normal(self):
        """Test exit code when no critical tasks"""
        with patch('sys.argv', ['next_task.py']):
            with patch('src.commands.next_task.NextTaskAnalyzer') as mock_analyzer:
                mock_instance = mock_analyzer.return_value
                mock_instance.analyze.return_value = [
                    Task("Normal", "Desc", 50, "medium", "action", "reason")
                ]
                mock_instance.format_output.return_value = "output"
                
                with patch('builtins.print'):
                    with pytest.raises(SystemExit) as exc_info:
                        from src.commands.next_task import main
                        main()
                
                assert exc_info.value.code == 0


# Import subprocess for timeout test
import subprocess