#!/usr/bin/env python3
"""
Next Task Analyzer - Intelligent work prioritization for AI Impact Model.

This module analyzes the repository state and suggests the next priority work item
based on multiple factors including git status, open issues, test failures, and TODOs.
"""

import subprocess
import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Task:
    """Represents a potential task with priority scoring."""
    title: str
    description: str
    priority: int  # 0-100 scale
    category: str  # 'critical', 'high', 'medium', 'low'
    action: str  # Specific command or action to take
    reasoning: str  # Why this task is important
    metadata: Dict[str, Any] = field(default_factory=dict)


class NextTaskAnalyzer:
    """Analyzes repository state to suggest next priority work."""
    
    PRIORITY_WEIGHTS = {
        'failing_tests': 100,
        'uncommitted_changes': 75,
        'unpushed_commits': 70,
        'open_prs': 60,
        'todo_comments': 50,
        'open_issues': 40,
        'stale_branches': 30,
        'documentation': 25,
        'performance': 20,
    }
    
    def __init__(self, repo_path: str = "."):
        """Initialize analyzer with repository path."""
        self.repo_path = Path(repo_path).resolve()
        self.tasks: List[Task] = []
        
    def run_command(self, cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                timeout=10
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def check_git_status(self) -> None:
        """Check for uncommitted changes."""
        returncode, stdout, _ = self.run_command(['git', 'status', '--porcelain'])
        
        if returncode == 0 and stdout.strip():
            lines = stdout.strip().split('\n')
            modified_files = [line[3:] for line in lines if line.startswith(' M')]
            added_files = [line[3:] for line in lines if line.startswith('??')]
            
            if modified_files:
                self.tasks.append(Task(
                    title="Commit uncommitted changes",
                    description=f"You have {len(modified_files)} modified file(s) that should be committed",
                    priority=self.PRIORITY_WEIGHTS['uncommitted_changes'],
                    category="high",
                    action="git add -A && git commit -m 'Your commit message'",
                    reasoning="Uncommitted changes should be saved to preserve work and maintain clean state",
                    metadata={'files': modified_files[:5]}  # First 5 files
                ))
            
            if added_files:
                self.tasks.append(Task(
                    title="Review untracked files",
                    description=f"You have {len(added_files)} untracked file(s)",
                    priority=30,
                    category="low",
                    action="git status",
                    reasoning="Untracked files might need to be added or ignored",
                    metadata={'files': added_files[:5]}
                ))
    
    def check_unpushed_commits(self) -> None:
        """Check for unpushed commits."""
        # Get current branch
        returncode, branch, _ = self.run_command(['git', 'branch', '--show-current'])
        if returncode != 0:
            return
            
        branch = branch.strip()
        
        # Check commits ahead of origin
        returncode, stdout, _ = self.run_command([
            'git', 'rev-list', '--count', f'origin/{branch}..HEAD'
        ])
        
        if returncode == 0:
            try:
                commits_ahead = int(stdout.strip())
                if commits_ahead > 0:
                    # Get commit messages
                    _, commit_msgs, _ = self.run_command([
                        'git', 'log', '--oneline', f'origin/{branch}..HEAD', '--max-count=5'
                    ])
                    
                    self.tasks.append(Task(
                        title="Push commits to remote",
                        description=f"You have {commits_ahead} unpushed commit(s) on {branch}",
                        priority=self.PRIORITY_WEIGHTS['unpushed_commits'],
                        category="high",
                        action="git push origin " + branch,
                        reasoning="Unpushed commits should be shared with the team and backed up",
                        metadata={'commits': commit_msgs.strip().split('\n') if commit_msgs else []}
                    ))
            except ValueError:
                pass
    
    def check_github_issues(self) -> None:
        """Check for open GitHub issues."""
        returncode, stdout, _ = self.run_command(['gh', 'issue', 'list', '--state', 'open', '--json', 'number,title,labels'])
        
        if returncode == 0 and stdout.strip():
            try:
                issues = json.loads(stdout)
                if issues:
                    # Prioritize by labels
                    high_priority_issues = [i for i in issues if any(
                        label.get('name', '').lower() in ['bug', 'critical', 'high-priority'] 
                        for label in i.get('labels', [])
                    )]
                    
                    if high_priority_issues:
                        issue = high_priority_issues[0]
                        self.tasks.append(Task(
                            title=f"Work on high-priority issue #{issue['number']}",
                            description=issue['title'],
                            priority=65,
                            category="medium",
                            action=f"gh issue view {issue['number']}",
                            reasoning="High-priority issues should be addressed promptly",
                            metadata={'issue_number': issue['number']}
                        ))
                    else:
                        # Regular issues
                        issue = issues[0]
                        self.tasks.append(Task(
                            title=f"Work on issue #{issue['number']}",
                            description=issue['title'],
                            priority=self.PRIORITY_WEIGHTS['open_issues'],
                            category="medium",
                            action=f"gh issue view {issue['number']}",
                            reasoning="Open issues represent planned work that needs completion",
                            metadata={'issue_number': issue['number'], 'total_issues': len(issues)}
                        ))
            except json.JSONDecodeError:
                pass
    
    def check_pull_requests(self) -> None:
        """Check for open pull requests."""
        returncode, stdout, _ = self.run_command(['gh', 'pr', 'list', '--state', 'open', '--json', 'number,title,author'])
        
        if returncode == 0 and stdout.strip():
            try:
                prs = json.loads(stdout)
                if prs:
                    pr = prs[0]
                    self.tasks.append(Task(
                        title=f"Review PR #{pr['number']}",
                        description=pr['title'],
                        priority=self.PRIORITY_WEIGHTS['open_prs'],
                        category="medium",
                        action=f"gh pr view {pr['number']}",
                        reasoning="Open PRs need review to maintain development velocity",
                        metadata={'pr_number': pr['number'], 'author': pr.get('author', {}).get('login', 'unknown')}
                    ))
            except json.JSONDecodeError:
                pass
    
    def check_test_status(self) -> None:
        """Check for failing tests."""
        returncode, stdout, stderr = self.run_command(['python', '-m', 'pytest', '--co', '-q'])
        
        if returncode != 0:
            # Tests failed to collect or other issue
            self.tasks.append(Task(
                title="Fix test collection errors",
                description="Tests are failing to collect properly",
                priority=self.PRIORITY_WEIGHTS['failing_tests'],
                category="critical",
                action="python -m pytest -v",
                reasoning="Test infrastructure must work for reliable development",
                metadata={'error': stderr[:200] if stderr else 'Unknown error'}
            ))
        else:
            # Run actual tests (quick check)
            returncode, stdout, stderr = self.run_command(['python', '-m', 'pytest', '-x', '--tb=no', '-q'])
            
            if returncode != 0:
                # Extract failure info
                failures = re.findall(r'FAILED (.*?) -', stdout)
                if failures:
                    self.tasks.append(Task(
                        title="Fix failing tests",
                        description=f"You have {len(failures)} failing test(s)",
                        priority=self.PRIORITY_WEIGHTS['failing_tests'],
                        category="critical",
                        action="python -m pytest -v --tb=short",
                        reasoning="Failing tests must be fixed to maintain code quality",
                        metadata={'failing_tests': failures[:5]}
                    ))
    
    def check_todo_comments(self) -> None:
        """Check for TODO/FIXME comments in code."""
        # Search for TODO comments in src directory
        returncode, stdout, _ = self.run_command([
            'grep', '-r', '-n', '-E', 'TODO|FIXME|XXX|HACK', 
            '--include=*.py', 'src/'
        ])
        
        if returncode == 0 and stdout.strip():
            todos = []
            for line in stdout.strip().split('\n')[:10]:  # First 10 TODOs
                match = re.match(r'(.*?):(\d+):(.*)', line)
                if match:
                    file_path, line_num, content = match.groups()
                    todos.append({
                        'file': file_path,
                        'line': line_num,
                        'content': content.strip()[:80]
                    })
            
            if todos:
                self.tasks.append(Task(
                    title=f"Address {len(todos)} TODO comment(s)",
                    description=f"Found TODO/FIXME comments that need attention",
                    priority=self.PRIORITY_WEIGHTS['todo_comments'],
                    category="medium",
                    action=f"grep -r -n -E 'TODO|FIXME' --include=*.py src/",
                    reasoning="TODO comments represent known technical debt",
                    metadata={'todos': todos[:3]}  # First 3 TODOs
                ))
    
    def check_documentation(self) -> None:
        """Check if documentation needs updating."""
        # Check if README was modified recently compared to code
        returncode, stdout, _ = self.run_command([
            'git', 'log', '-1', '--format=%ct', 'README.md'
        ])
        
        if returncode == 0:
            try:
                readme_timestamp = int(stdout.strip())
                readme_date = datetime.fromtimestamp(readme_timestamp)
                
                # Check last code change
                returncode, stdout, _ = self.run_command([
                    'git', 'log', '-1', '--format=%ct', 'src/'
                ])
                
                if returncode == 0:
                    code_timestamp = int(stdout.strip())
                    code_date = datetime.fromtimestamp(code_timestamp)
                    
                    if code_date > readme_date + timedelta(days=3):
                        self.tasks.append(Task(
                            title="Update README documentation",
                            description="README may be outdated compared to recent code changes",
                            priority=self.PRIORITY_WEIGHTS['documentation'],
                            category="low",
                            action="Review and update README.md",
                            reasoning="Documentation should stay in sync with code changes",
                            metadata={
                                'readme_last_updated': readme_date.strftime('%Y-%m-%d'),
                                'code_last_updated': code_date.strftime('%Y-%m-%d')
                            }
                        ))
            except (ValueError, OSError):
                pass
    
    def analyze(self) -> List[Task]:
        """Run all checks and return prioritized task list."""
        self.tasks = []
        
        # Run all checks
        self.check_test_status()
        self.check_git_status()
        self.check_unpushed_commits()
        self.check_github_issues()
        self.check_pull_requests()
        self.check_todo_comments()
        self.check_documentation()
        
        # Sort by priority (highest first)
        self.tasks.sort(key=lambda t: t.priority, reverse=True)
        
        return self.tasks
    
    def format_output(self, tasks: List[Task], verbose: bool = False) -> str:
        """Format tasks for console output."""
        if not tasks:
            return "✅ All clear! No immediate tasks found. Consider:\n" \
                   "  • Review code quality\n" \
                   "  • Add more tests\n" \
                   "  • Optimize performance\n" \
                   "  • Update documentation"
        
        output = []
        
        # Primary recommendation
        primary = tasks[0]
        output.append("🎯 NEXT PRIORITY TASK")
        output.append("=" * 50)
        output.append(f"\n📌 {primary.title}")
        output.append(f"   {primary.description}")
        output.append(f"\n   Priority: {self._format_priority(primary.priority, primary.category)}")
        output.append(f"   Action:   {primary.action}")
        output.append(f"   Why:      {primary.reasoning}")
        
        if primary.metadata and verbose:
            output.append("\n   Details:")
            for key, value in primary.metadata.items():
                if isinstance(value, list):
                    output.append(f"     {key}:")
                    for item in value[:3]:
                        output.append(f"       • {item}")
                else:
                    output.append(f"     {key}: {value}")
        
        # Other tasks
        if len(tasks) > 1:
            output.append("\n\n📋 OTHER TASKS")
            output.append("-" * 50)
            
            for task in tasks[1:6]:  # Next 5 tasks
                priority_str = self._format_priority(task.priority, task.category)
                output.append(f"\n  {priority_str} {task.title}")
                output.append(f"       {task.description}")
                if verbose:
                    output.append(f"       → {task.action}")
        
        # Quick stats
        output.append("\n\n📊 REPOSITORY HEALTH")
        output.append("-" * 50)
        
        stats = self._get_quick_stats(tasks)
        for stat in stats:
            output.append(f"  {stat}")
        
        return "\n".join(output)
    
    def _format_priority(self, priority: int, category: str) -> str:
        """Format priority with color/emoji indicators."""
        if category == "critical":
            return f"🔴 CRITICAL ({priority})"
        elif category == "high":
            return f"🟠 HIGH ({priority})"
        elif category == "medium":
            return f"🟡 MEDIUM ({priority})"
        else:
            return f"🟢 LOW ({priority})"
    
    def _get_quick_stats(self, tasks: List[Task]) -> List[str]:
        """Get quick repository health statistics."""
        stats = []
        
        # Test status
        has_test_failures = any(t.category == "critical" and "test" in t.title.lower() for t in tasks)
        if has_test_failures:
            stats.append("❌ Tests failing")
        else:
            stats.append("✅ Tests passing")
        
        # Git status
        uncommitted = sum(1 for t in tasks if "uncommitted" in t.title.lower())
        unpushed = sum(1 for t in tasks if "push" in t.title.lower())
        
        if uncommitted:
            stats.append(f"⚠️  {uncommitted} uncommitted change set(s)")
        if unpushed:
            stats.append(f"⬆️  Commits ready to push")
        
        # Issues/PRs
        issues = sum(1 for t in tasks if "issue" in t.title.lower())
        prs = sum(1 for t in tasks if "PR" in t.title)
        
        if issues:
            stats.append(f"📝 {issues} open issue(s)")
        if prs:
            stats.append(f"🔄 {prs} open PR(s)")
        
        # TODOs
        todos = sum(1 for t in tasks if "TODO" in t.title)
        if todos:
            stats.append(f"📌 TODO comments found")
        
        return stats if stats else ["✨ Repository is in good shape!"]


def main():
    """Main entry point for the next task command."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze repository and suggest next priority task"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed information about tasks'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all discovered tasks'
    )
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = NextTaskAnalyzer()
    tasks = analyzer.analyze()
    
    if args.json:
        # JSON output
        output = {
            'tasks': [
                {
                    'title': t.title,
                    'description': t.description,
                    'priority': t.priority,
                    'category': t.category,
                    'action': t.action,
                    'reasoning': t.reasoning,
                    'metadata': t.metadata
                }
                for t in tasks
            ],
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        if args.all:
            # Show all tasks
            for i, task in enumerate(tasks, 1):
                print(f"\n{'='*50}")
                print(f"Task #{i}: {task.title}")
                print(f"Priority: {task.priority} ({task.category})")
                print(f"Description: {task.description}")
                print(f"Action: {task.action}")
                print(f"Reasoning: {task.reasoning}")
                if task.metadata:
                    print(f"Metadata: {task.metadata}")
        else:
            # Standard output
            output = analyzer.format_output(tasks, verbose=args.verbose)
            print(output)
    
    # Exit with appropriate code
    if tasks and tasks[0].category == "critical":
        sys.exit(1)  # Critical task pending
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()