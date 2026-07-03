"""
Tests for Agent Skills.
Verifies skill loading, trigger descriptions, and structure (Day 3).
"""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


class TestSkillStructure:
    """Day 3: Verify Agent Skills follow the standard format."""

    SKILLS = ["data-analysis", "insight-generation", "report-writing"]

    def test_skill_directories_exist(self):
        """Each skill has its own directory."""
        for skill in self.SKILLS:
            skill_dir = os.path.join(PROJECT_ROOT, "skills", skill)
            assert os.path.isdir(skill_dir), f"Missing skill directory: {skill}"

    def test_skill_md_exists(self):
        """Each skill has a SKILL.md file (mandatory)."""
        for skill in self.SKILLS:
            skill_md = os.path.join(PROJECT_ROOT, "skills", skill, "SKILL.md")
            assert os.path.isfile(skill_md), f"Missing SKILL.md for: {skill}"

    def test_skill_yaml_frontmatter(self):
        """Day 3: SKILL.md must have YAML frontmatter with name and description."""
        for skill in self.SKILLS:
            skill_md = os.path.join(PROJECT_ROOT, "skills", skill, "SKILL.md")
            with open(skill_md) as f:
                content = f.read()
            assert content.startswith("---"), f"SKILL.md for '{skill}' missing YAML frontmatter"
            end = content.index("---", 3)
            frontmatter = content[3:end].strip()
            assert "name:" in frontmatter, f"Missing 'name' in '{skill}' frontmatter"
            assert "description:" in frontmatter, f"Missing 'description' in '{skill}' frontmatter"

    def test_skill_description_has_trigger_keywords(self):
        """Day 3: Description should contain trigger keywords for routing."""
        for skill in self.SKILLS:
            skill_md = os.path.join(PROJECT_ROOT, "skills", skill, "SKILL.md")
            with open(skill_md) as f:
                content = f.read()
            end = content.index("---", 3)
            frontmatter = content[3:end].strip()
            # Description should mention what triggers it
            assert "Use when" in frontmatter or "Trigger" in frontmatter, \
                f"Skill '{skill}' description lacks trigger guidance"

    def test_skill_description_has_negative_trigger(self):
        """Day 3: Description should state what it's NOT for (prevents over-triggering)."""
        for skill in self.SKILLS:
            skill_md = os.path.join(PROJECT_ROOT, "skills", skill, "SKILL.md")
            with open(skill_md) as f:
                content = f.read()
            end = content.index("---", 3)
            frontmatter = content[3:end].strip()
            # Should have negative trigger
            assert "Do NOT" in frontmatter or "not for" in frontmatter.lower(), \
                f"Skill '{skill}' description lacks negative trigger (over-triggering risk)"

    def test_data_analysis_has_scripts(self):
        """Day 3: data-analysis skill should have scripts directory."""
        scripts_dir = os.path.join(PROJECT_ROOT, "skills", "data-analysis", "scripts")
        assert os.path.isdir(scripts_dir)
        assert os.path.isfile(os.path.join(scripts_dir, "analyze.py"))

    def test_data_analysis_has_references(self):
        """Day 3: data-analysis skill should have references directory."""
        ref_dir = os.path.join(PROJECT_ROOT, "skills", "data-analysis", "references")
        assert os.path.isdir(ref_dir)
        assert os.path.isfile(os.path.join(ref_dir, "methods.md"))

    def test_report_writing_has_template(self):
        """Day 3: report-writing skill should have a template in assets."""
        assets_dir = os.path.join(PROJECT_ROOT, "skills", "report-writing", "assets")
        assert os.path.isdir(assets_dir)
        assert os.path.isfile(os.path.join(assets_dir, "report_template.md"))

    def test_insight_generation_has_frameworks(self):
        """Day 3: insight-generation skill should reference analysis frameworks."""
        ref_dir = os.path.join(PROJECT_ROOT, "skills", "insight-generation", "references")
        assert os.path.isdir(ref_dir)
        content = open(os.path.join(ref_dir, "frameworks.md")).read()
        assert "Pareto" in content or "SWOT" in content


class TestSkillLoading:
    """Test the skill loading mechanism (Progressive Disclosure)."""

    def test_load_skill_returns_content(self):
        """Skills can be loaded and contain methodology text."""
        skill_md = os.path.join(PROJECT_ROOT, "skills", "data-analysis", "SKILL.md")
        with open(skill_md) as f:
            content = f.read()
        # Should have methodology steps
        assert "Step 1" in content or "step 1" in content.lower()
        # Should reference MCP tools
        assert "MCP" in content or "tool" in content.lower()

    def test_skill_body_not_empty(self):
        """Skill body (after frontmatter) should contain instructions."""
        for skill in ["data-analysis", "insight-generation", "report-writing"]:
            skill_md = os.path.join(PROJECT_ROOT, "skills", skill, "SKILL.md")
            with open(skill_md) as f:
                content = f.read()
            # Find end of frontmatter
            end = content.index("---", 3)
            body = content[end + 3:].strip()
            assert len(body) > 100, f"Skill '{skill}' body is too short ({len(body)} chars)"

    def test_skill_metadata_is_small(self):
        """Day 3: Metadata (frontmatter) should be small for context efficiency."""
        for skill in ["data-analysis", "insight-generation", "report-writing"]:
            skill_md = os.path.join(PROJECT_ROOT, "skills", skill, "SKILL.md")
            with open(skill_md) as f:
                content = f.read()
            end = content.index("---", 3)
            metadata = content[3:end].strip()
            # Metadata should be < 500 chars (lightweight for always-in-context)
            assert len(metadata) < 500, f"Skill '{skill}' metadata too large ({len(metadata)} chars)"