"""
Comprehensive tests for the ReviewCommand module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from src.commands.review_command import ReviewCommand


class TestReviewCommand:
    """Test the ReviewCommand class"""
    
    @pytest.fixture
    def review_command(self, tmp_path):
        """Create ReviewCommand with temp directory"""
        return ReviewCommand(str(tmp_path))
    
    def test_initialization(self, tmp_path):
        """Test ReviewCommand initialization"""
        reviewer = ReviewCommand(str(tmp_path))
        
        assert reviewer.repo_path == tmp_path
        assert reviewer.reports_dir == tmp_path / ".claude" / "agents" / "reports"
        assert reviewer.timestamp is not None
    
    def test_ensure_reports_directory(self, review_command, tmp_path):
        """Test reports directory creation"""
        review_command.ensure_reports_directory()
        
        reports_dir = tmp_path / ".claude" / "agents" / "reports"
        assert reports_dir.exists()
        assert reports_dir.is_dir()
        
        gitignore = reports_dir / ".gitignore"
        assert gitignore.exists()
        assert "*.md" in gitignore.read_text()
    
    def test_ensure_reports_directory_existing(self, review_command, tmp_path):
        """Test reports directory when it already exists"""
        reports_dir = tmp_path / ".claude" / "agents" / "reports"
        reports_dir.mkdir(parents=True)
        gitignore = reports_dir / ".gitignore"
        gitignore.write_text("existing content")
        
        review_command.ensure_reports_directory()
        
        # Should not overwrite existing gitignore
        assert gitignore.read_text() == "existing content"
    
    def test_run_python_reviewer(self, review_command):
        """Test running Python reviewer agent"""
        results = review_command.run_python_reviewer(verbose=False)
        
        assert results["agent"] == "python-reviewer"
        assert "timestamp" in results
        assert results["overall_score"] == 8.5
        assert "findings" in results
        assert "metrics" in results
        assert "strengths" in results
        
        # Check findings structure
        assert "high_priority" in results["findings"]
        assert "medium_priority" in results["findings"]
        assert "low_priority" in results["findings"]
    
    def test_run_python_reviewer_verbose(self, review_command):
        """Test running Python reviewer with verbose output"""
        with patch('builtins.print') as mock_print:
            results = review_command.run_python_reviewer(verbose=True)
            
            # Should print verbose output
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Analyzed" in call for call in print_calls)
            assert any("Overall score" in call for call in print_calls)
    
    def test_run_testing_expert(self, review_command):
        """Test running testing expert agent"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout="test1\ntest2\ntest3",
                stderr="",
                returncode=0
            )
            
            results = review_command.run_testing_expert(verbose=False)
            
            assert results["agent"] == "python-testing-expert"
            assert "timestamp" in results
            assert results["test_health_score"] == 7.8
            assert "findings" in results
            assert "metrics" in results
            assert "recommendations" in results
    
    def test_run_testing_expert_verbose(self, review_command):
        """Test running testing expert with verbose output"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout="test1\ntest2",
                stderr="",
                returncode=0
            )
            
            with patch('builtins.print') as mock_print:
                results = review_command.run_testing_expert(verbose=True)
                
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("Found" in call and "tests" in call for call in print_calls)
                assert any("Coverage" in call for call in print_calls)
    
    def test_generate_summary_report(self, review_command):
        """Test generating summary report"""
        reviewer_results = {
            "overall_score": 8.5,
            "findings": {
                "high_priority": [
                    {
                        "issue": "Performance",
                        "description": "Needs caching",
                        "recommendation": "Add caching",
                        "status": "open"
                    }
                ],
                "medium_priority": [],
                "low_priority": []
            },
            "metrics": {
                "files_analyzed": 42,
                "total_lines": 5000,
                "complexity_score": "B+",
                "maintainability_index": 78
            },
            "strengths": ["Good structure", "Clean code"],
            "improvements_since_last_review": ["Added tests"]
        }
        
        testing_results = {
            "test_health_score": 7.5,
            "findings": {
                "coverage_gaps": [
                    {
                        "module": "src/test.py",
                        "coverage": "50%",
                        "priority": "high",
                        "recommendation": "Add tests"
                    }
                ],
                "test_patterns": [
                    {
                        "pattern": "Good fixtures",
                        "type": "positive"
                    }
                ]
            },
            "metrics": {
                "total_tests": 100,
                "test_coverage": {
                    "overall": "75%"
                },
                "test_to_code_ratio": "1:3",
                "average_test_time": "0.1s"
            },
            "recommendations": [
                {
                    "priority": "high",
                    "category": "Coverage",
                    "action": "Increase coverage"
                }
            ]
        }
        
        report = review_command.generate_summary_report(reviewer_results, testing_results)
        
        assert "# Code Review Summary Report" in report
        assert "Executive Summary" in report
        assert "8.5/10" in report
        assert "7.5/10" in report
        assert "Combined Quality Score: 8.0/10" in report
        assert "Production Ready" in report
        assert "Key Findings" in report
        assert "Strengths" in report
        assert "Metrics Summary" in report
        assert "Top Recommendations" in report
    
    def test_generate_summary_report_low_score(self, review_command):
        """Test summary report with low scores"""
        reviewer_results = {
            "overall_score": 4.0,
            "findings": {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": []
            },
            "metrics": {
                "files_analyzed": 10,
                "total_lines": 1000,
                "complexity_score": "D",
                "maintainability_index": 40
            },
            "strengths": []
        }
        
        testing_results = {
            "test_health_score": 3.0,
            "findings": {
                "coverage_gaps": [],
                "test_patterns": []
            },
            "metrics": {
                "total_tests": 5,
                "test_coverage": {"overall": "20%"},
                "test_to_code_ratio": "1:20",
                "average_test_time": "5s"
            },
            "recommendations": []
        }
        
        report = review_command.generate_summary_report(reviewer_results, testing_results)
        
        assert "Combined Quality Score: 3.5/10" in report
        assert "❌ **Status**: Significant Issues" in report
    
    def test_save_reports(self, review_command, tmp_path):
        """Test saving reports to files"""
        review_command.ensure_reports_directory()
        
        reviewer_results = {"test": "reviewer"}
        testing_results = {"test": "testing"}
        summary = "# Summary Report\nTest content"
        
        reviewer_path, testing_path, summary_path = review_command.save_reports(
            reviewer_results, testing_results, summary
        )
        
        # Check files were created
        assert reviewer_path.exists()
        assert testing_path.exists()
        assert summary_path.exists()
        
        # Check content
        assert json.loads(reviewer_path.read_text()) == reviewer_results
        assert json.loads(testing_path.read_text()) == testing_results
        assert summary_path.read_text() == summary
        
        # Check latest symlink/copy
        latest_path = review_command.reports_dir / "latest_review.md"
        assert latest_path.exists()
    
    def test_run_full_workflow(self, review_command):
        """Test complete review workflow"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout="test1\ntest2",
                stderr="",
                returncode=0
            )
            
            with patch('builtins.print'):
                exit_code = review_command.run(verbose=False, show_report=False)
                
                assert exit_code == 0
                
                # Check reports were created
                reports_dir = review_command.reports_dir
                assert reports_dir.exists()
                
                # Check for report files
                md_files = list(reports_dir.glob("*.md"))
                json_files = list(reports_dir.glob("*.json"))
                
                assert len(md_files) >= 1
                assert len(json_files) >= 2
    
    def test_run_with_show_report(self, review_command):
        """Test running with report display"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout="test1",
                stderr="",
                returncode=0
            )
            
            with patch('builtins.print') as mock_print:
                exit_code = review_command.run(verbose=False, show_report=True)
                
                # Should print the report
                print_output = str(mock_print.call_args_list)
                assert "Code Review Summary Report" in print_output
    
    def test_run_with_low_score_exit_code(self, review_command):
        """Test exit code when score is low"""
        # Mock low scores
        with patch.object(review_command, 'run_python_reviewer') as mock_reviewer:
            mock_reviewer.return_value = {
                "overall_score": 3.0,
                "findings": {"high_priority": [], "medium_priority": [], "low_priority": []},
                "metrics": {"files_analyzed": 1, "total_lines": 100, 
                           "complexity_score": "F", "maintainability_index": 20},
                "strengths": []
            }
            
            with patch.object(review_command, 'run_testing_expert') as mock_testing:
                mock_testing.return_value = {
                    "test_health_score": 2.0,
                    "findings": {"coverage_gaps": [], "test_patterns": []},
                    "metrics": {"total_tests": 0, "test_coverage": {"overall": "0%"},
                               "test_to_code_ratio": "0:1", "average_test_time": "0s"},
                    "recommendations": []
                }
                
                with patch('builtins.print'):
                    exit_code = review_command.run(verbose=False, show_report=False)
                    
                    assert exit_code == 1  # Should fail with low score


class TestReviewCommandMain:
    """Test the main function"""
    
    def test_main_default_args(self):
        """Test main with default arguments"""
        with patch('sys.argv', ['review_command.py']):
            with patch('src.commands.review_command.ReviewCommand') as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.run.return_value = 0
                
                with patch('sys.exit') as mock_exit:
                    from src.commands.review_command import main
                    main()
                    
                    mock_instance.run.assert_called_with(verbose=False, show_report=True)
                    mock_exit.assert_called_with(0)
    
    def test_main_verbose_flag(self):
        """Test main with verbose flag"""
        with patch('sys.argv', ['review_command.py', '-v']):
            with patch('src.commands.review_command.ReviewCommand') as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.run.return_value = 0
                
                with patch('sys.exit'):
                    from src.commands.review_command import main
                    main()
                    
                    mock_instance.run.assert_called_with(verbose=True, show_report=True)
    
    def test_main_no_show_flag(self):
        """Test main with no-show flag"""
        with patch('sys.argv', ['review_command.py', '--no-show']):
            with patch('src.commands.review_command.ReviewCommand') as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.run.return_value = 0
                
                with patch('sys.exit'):
                    from src.commands.review_command import main
                    main()
                    
                    mock_instance.run.assert_called_with(verbose=False, show_report=False)
    
    def test_main_custom_path(self):
        """Test main with custom path"""
        with patch('sys.argv', ['review_command.py', '--path', '/custom/path']):
            with patch('src.commands.review_command.ReviewCommand') as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.run.return_value = 0
                
                with patch('sys.exit'):
                    from src.commands.review_command import main
                    main()
                    
                    mock_class.assert_called_with('/custom/path')
    
    def test_main_combined_flags(self):
        """Test main with multiple flags"""
        with patch('sys.argv', ['review_command.py', '-v', '--show', '--path', '/test']):
            with patch('src.commands.review_command.ReviewCommand') as mock_class:
                mock_instance = mock_class.return_value
                mock_instance.run.return_value = 1
                
                with patch('sys.exit') as mock_exit:
                    from src.commands.review_command import main
                    main()
                    
                    mock_class.assert_called_with('/test')
                    mock_instance.run.assert_called_with(verbose=True, show_report=True)
                    mock_exit.assert_called_with(1)