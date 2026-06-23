import os
import re
from pathlib import Path

# 技能文件存放目录
SKILLS_DIR = Path(__file__).parent / "skills"
_skill_cache = {}


def _parse_skill_file(file_path):
    """读取并解析 SKILL.md 文件，返回 (正文内容, 元数据字典)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # 检测 YAML frontmatter（以 --- 开头）
    if raw.startswith('---'):
        parts = raw.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            body = parts[2].strip()
            # 简单解析键值对
            metadata = {}
            for line in frontmatter.splitlines():
                line = line.strip()
                if ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip()
            return body, metadata

    # 没有 frontmatter，整个文件作为内容
    return raw, {}


def load_all_skills():
    """扫描 skills/ 目录，加载所有 .md 文件，返回缓存字典"""
    if _skill_cache:
        return _skill_cache

    # 如果 skills 目录不存在，自动创建一个默认的通用专家
    if not SKILLS_DIR.exists():
        os.makedirs(SKILLS_DIR, exist_ok=True)
        # 写入一个默认的通用分析师 Skill
        default_skill_path = SKILLS_DIR / "通用分析师_SKILL.md"
        with open(default_skill_path, 'w', encoding='utf-8') as f:
            f.write("""---
tags: [通用, 基本面分析]
author: 系统
---
你是一位专业的股票分析师，擅长从基本面和技术面综合分析公司价值。
你的分析风格：客观、全面、数据驱动。
在分析时，请重点关注：
1. 公司的盈利能力（营收、净利润、ROE）
2. 估值水平（PE、PB是否合理）
3. 成长性（营收和利润增速）
4. 潜在风险（负债率、行业竞争）
请给出清晰的投资结论和理由。""")
        print("⚠️ 未找到 skills/ 文件夹，已自动创建默认的'通用分析师'。")

    for md_file in SKILLS_DIR.glob("*.md"):
        expert_name = md_file.stem.replace('_SKILL', '')  # 去除 _SKILL 后缀，显示更清爽
        content, metadata = _parse_skill_file(md_file)
        _skill_cache[expert_name] = {
            "content": content,
            "metadata": metadata,
            "file_path": str(md_file)
        }
    return _skill_cache


def list_experts():
    """返回所有可用专家名称列表"""
    skills = load_all_skills()
    return sorted(skills.keys())


def load_skill(expert_name: str):
    """根据专家名称加载技能内容，如果不存在则抛出 ValueError"""
    skills = load_all_skills()
    # 尝试精确匹配
    if expert_name in skills:
        return skills[expert_name]["content"]

    # 尝试模糊匹配（防止文件名和显示名不完全一致）
    for key in skills.keys():
        if expert_name in key or key in expert_name:
            return skills[key]["content"]

    raise ValueError(f"未找到名为 '{expert_name}' 的技能，可用: {list_experts()}")


def get_expert_metadata(expert_name: str):
    """获取专家的元数据"""
    skills = load_all_skills()
    for key, val in skills.items():
        if expert_name in key or key in expert_name:
            return val.get("metadata", {})
    return {}