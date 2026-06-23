import os
import json
import logging
import random
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not API_KEY:
    raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com"
)


def generate_mock_analysis(stock_text: str, expert_name: str = "专家"):
    """
    生成模拟分析结果，用于演示或降级场景
    针对不同专家生成更具体的摘要
    """
    lines = stock_text.split('\n')
    stock_name = ""
    price = ""
    pe = ""
    pb = ""
    for line in lines:
        if '名称' in line or '股票名称' in line:
            stock_name = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
        if '最新价' in line:
            price = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
        if '市盈率' in line:
            pe = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()
        if '市净率' in line:
            pb = line.split('：')[-1].strip() if '：' in line else line.split(':')[-1].strip()

    if not stock_name:
        stock_name = "该股票"

    # ===== 根据专家名称生成更具体的摘要 =====
    if "格雷厄姆" in expert_name:
        summary = f"{stock_name}当前PE={pe}，PB={pb}，PE×PB需进一步核实。根据格雷厄姆防御型标准，当前估值需结合历史分位判断，安全边际需补充更多财务数据。建议关注：流动比率、长期负债、股息连续派发记录。"
        valuation = f"PE={pe}，需对比历史均值"
        growth = "数据不足，需核查营收和利润增速"
        health = "流动比率和长期负债数据缺失，需进一步核实"
        risk_detail = "公司层面：财务数据不完整，需核实负债率和现金流；行业层面：行业竞争格局变化；市场层面：估值回调风险"

    elif "欧奈尔" in expert_name:
        summary = f"{stock_name}当前价格{price}，CAN SLIM体系核心指标待验证。C（当期收益）和A（年度收益）数据缺失，需重点核查财报。L（行业龙头地位）和I（机构认同度）需进一步分析。"
        valuation = "估值需结合成长性综合判断"
        growth = "CAN SLIM核心指标，数据待核实"
        health = "财务数据需进一步核查"
        risk_detail = "公司层面：成长性验证不足；行业层面：行业竞争加剧；市场层面：市场风格切换风险"

    elif "彼得·林奇" in expert_name or "林奇" in expert_name:
        summary = f"{stock_name}需先判断公司类型（缓慢增长/稳定增长/快速增长/周期型/困境反转型）。当前PE={pe}，PEG数据缺失无法准确评估。彼得·林奇偏好PEG<1的成长股，建议获取完整财报后重新评估。"
        valuation = f"PEG是核心指标，当前PE={pe}，需配合增速计算PEG"
        growth = "需判断公司所属类型（缓慢/稳定/快速增长）"
        health = "财务数据需进一步核查，关注负债率和现金流"
        risk_detail = "公司层面：成长性不确定；行业层面：行业天花板；市场层面：市场情绪波动"

    elif "巴菲特" in expert_name or "沃伦·巴菲特" in expert_name:
        summary = f"{stock_name}当前PE={pe}，PB={pb}。巴菲特注重护城河、ROE和合理价格。当前ROE数据待核实，若ROE持续>15%且估值合理，则符合选股标准。建议关注：长期竞争优势、管理层质量、自由现金流。"
        valuation = f"PE={pe}，需判断是否在合理区间（参考无风险利率）"
        growth = "ROE是核心指标，数据待核实"
        health = "关注自由现金流和负债率"
        risk_detail = "公司层面：护城河宽度判断；行业层面：行业变革风险；市场层面：系统性风险"

    elif "惠特尼·乔治" in expert_name or "惠特尼" in expert_name:
        summary = f"{stock_name}当前PE={pe}，PB={pb}。惠特尼·乔治深度价值标准要求PB<0.8、股息率>4%、安全边际>40%。当前PB={pb}，需判断是否低于0.8门槛；股息率和隐蔽资产数据待核实。建议核查资产负债表中的隐蔽资产（土地、股权投资、品牌价值）及公司是否处于困境反转阶段。"
        valuation = f"PB={pb}，需判断是否<0.8（深度价值核心门槛）"
        growth = "深度价值策略更关注资产质量和股息，而非高成长"
        health = "需核查：流动比率(>2)、长期负债率(<40%)、自由现金流覆盖率"
        risk_detail = "公司层面：资产质量风险、股息可持续性；行业层面：行业周期底部风险；市场层面：价值陷阱风险（需区分低估值与真价值）"

    else:
        valuation_rand = random.choice(["偏高", "合理", "偏低"])
        growth_rand = random.choice(["强", "一般", "弱"])
        health_rand = random.choice(["健康", "一般", "较差"])
        summary = f"{stock_name}当前估值{valuation_rand}，成长性{growth_rand}，财务状况{health_rand}。市场情绪中性，建议关注后续财报和行业政策。"
        risk_detail = "公司层面：经营风险中等；行业层面：竞争加剧；市场层面：市场波动风险"

    # 随机生成一些数据（保持多样性）
    valuation_choices = ["偏高", "合理", "偏低"]
    growth_choices = ["强", "一般", "弱"]
    health_choices = ["健康", "一般", "较差"]
    tech_choices = ["强势", "震荡", "弱势"]
    advice_choices = ["关注", "观望", "回避"]

    return {
        "summary": summary,
        "key_metrics_analysis": {
            "估值": f"估值{random.choice(valuation_choices)}，需结合具体指标判断",
            "成长性": f"成长性{random.choice(growth_choices)}，建议核查核心数据",
            "财务健康": f"财务状态{random.choice(health_choices)}，建议进一步分析",
            "技术面": f"近期走势{random.choice(tech_choices)}，成交量一般"
        },
        "industry_comparison": f"与同业相比，该股票估值{random.choice(valuation_choices)}，成长性{random.choice(growth_choices)}，整体竞争力中等。",
        "risk_analysis": {
            "公司层面": risk_detail.split("；")[0] if "；" in risk_detail else "经营风险中等，财务数据需核实",
            "行业层面": risk_detail.split("；")[1] if "；" in risk_detail else "行业竞争加剧，政策影响需关注",
            "市场层面": risk_detail.split("；")[2] if "；" in risk_detail else "市场波动风险，流动性一般"
        },
        "opportunities": "1. 行业景气度提升；2. 公司新产品放量。",
        "investment_conclusion": {
            "综合评级": random.choice(["中性", "关注", "观望"]),
            "核心逻辑": "估值合理，成长性待验证。",
            "建议关注": "下季度财报及行业政策动向。"
        }
    }


def extract_expert_info(skill_content: str):
    """从 Skill 内容中提取专家名称和分析框架关键词"""
    author_match = re.search(r'author:\s*(.+)', skill_content)
    if author_match:
        expert_name = author_match.group(1).strip()
    else:
        lines = skill_content.split('\n')
        expert_name = "该专家"
        for line in lines[:10]:
            name_match = re.search(r'你是一位?[遵循的]*\s*([^，,。\n]{2,10})?', line)
            if name_match and name_match.group(1):
                candidate = name_match.group(1).strip()
                if len(candidate) > 1 and not candidate.startswith('该'):
                    expert_name = candidate
                    break
            full_name_match = re.search(r'([本彼乔威惠][\u4e00-\u9fa5]{1,3}·[\u4e00-\u9fa5]{1,3})', line)
            if full_name_match:
                expert_name = full_name_match.group(1)
                break

    content_lower = skill_content.lower()
    if any(k in skill_content for k in ['安全边际', '格雷厄姆', '防御型', 'pe×pb']):
        keywords = ["安全边际", "防御型投资", "PE×PB < 22.5", "股息记录"]
    elif any(k in skill_content for k in ['CAN SLIM', '欧奈尔', '当期收益', '龙头股']):
        keywords = ["CAN SLIM", "当期收益(C)", "年度收益(A)", "龙头股(L)", "机构认同(I)"]
    elif any(k in skill_content for k in ['PEG', '彼得·林奇', '公司分类', '六类避而不买']):
        keywords = ["PEG估值", "公司分类", "增长型", "六类避而不买"]
    elif any(k in skill_content for k in ['深度价值', '惠特尼·乔治', '低估值', '高股息', '隐蔽资产']):
        keywords = ["深度价值", "低PB(<0.8)", "高股息(>4%)", "隐蔽资产", "安全边际(>40%)"]
    elif any(k in skill_content for k in ['护城河', '巴菲特', 'ROE']):
        keywords = ["护城河", "长期持有", "ROE", "合理价格"]
    else:
        keywords = ["估值分析", "财务稳健性", "成长性"]

    return expert_name, keywords


def analyze_with_expert(stock_text: str, expert_skill: str):
    """使用指定专家的技能对股票数据进行分析"""
    expert_name, keywords = extract_expert_info(expert_skill)

    system_prompt = f"""{expert_skill}

你是一位遵循 {expert_name} 投资理念的专业分析师。

请对提供的股票数据进行分析，并严格按以下 JSON 格式输出（不要输出其他任何内容）：
{{
    "summary": "基于{expert_name}的分析框架，给出核心结论。必须包含该框架的核心指标和判断标准。如果数据不足，请明确指出缺失项并给出保守估计。",
    "key_metrics_analysis": {{
        "估值": "按照{expert_name}的估值方法进行判断，给出具体数值和参照",
        "成长性": "从{expert_name}的视角评价成长性，指出关键观测指标",
        "财务健康": "按照{expert_name}的标准评价财务稳健性",
        "技术面": "分析近期价格走势和成交量（如果该专家重视技术面）"
    }},
    "industry_comparison": "将该股票与同行业公司对比，指出相对优势和劣势",
    "risk_analysis": {{
        "公司层面": "经营风险、财务风险、管理层风险等",
        "行业层面": "竞争格局、政策风险、技术替代风险等",
        "市场层面": "流动性风险、估值回调风险等"
    }},
    "opportunities": "列举2-3个可能驱动股价上涨的催化剂或逻辑",
    "investment_conclusion": {{
        "综合评级": "强烈看好 / 看好 / 中性 / 谨慎 / 回避",
        "核心逻辑": "用一句话总结最核心的看好或看空逻辑",
        "建议关注": "需要进一步跟踪的关键指标或事件"
    }}
}}
"""

    user_prompt = f"""
请严格遵循 {expert_name} 的分析框架，对以下股票数据进行专业、深度的分析。

分析框架核心关键词：{', '.join(keywords)}

数据来源：Baostock（实时行情 + 部分财务指标）
数据内容：
{stock_text}

分析要求：
1. 必须按照 {expert_name} 的框架逐一评估关键指标。
2. 摘要部分必须体现该专家的核心判断标准。
3. 对于缺失的数据，请明确标注"数据缺失"，并说明该信息对最终判断的影响程度。
4. 估值判断要给出具体参照。
5. 风险分析要有层次感，区分公司层面、行业层面、市场层面。
6. 结论要明确给出是否符合该专家投资标准的判断。
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            timeout=15
        )

        raw_result = response.choices[0].message.content
        logging.info(f"AI原始返回: {raw_result[:500]}...")

        try:
            result = json.loads(raw_result)
            required_fields = ['summary', 'key_metrics_analysis', 'risk_analysis', 'investment_conclusion']
            missing_fields = [f for f in required_fields if f not in result]
            if missing_fields:
                logging.warning(f"JSON缺少字段: {missing_fields}，将补充默认值")
                if 'key_metrics_analysis' not in result:
                    result['key_metrics_analysis'] = {"估值": "数据不足", "成长性": "数据不足", "财务健康": "数据不足",
                                                      "技术面": "数据不足"}
                if 'risk_analysis' not in result:
                    result['risk_analysis'] = {"公司层面": "待补充", "行业层面": "待补充", "市场层面": "待补充"}
                if 'investment_conclusion' not in result:
                    result['investment_conclusion'] = {"综合评级": "待评估", "核心逻辑": "待补充", "建议关注": "待补充"}
            return result
        except json.JSONDecodeError as e:
            logging.warning(f"JSON解析失败: {e}，将展示原始内容")
            return {
                "summary": "AI返回内容（非标准JSON格式，已展示原始输出）：",
                "key_metrics_analysis": {"估值": "请查看下方原始输出", "成长性": "请查看下方原始输出",
                                         "财务健康": "请查看下方原始输出", "技术面": "请查看下方原始输出"},
                "industry_comparison": "请查看下方原始输出",
                "risk_analysis": {"公司层面": "请查看下方原始输出", "行业层面": "请查看下方原始输出",
                                  "市场层面": "请查看下方原始输出"},
                "opportunities": "请查看下方原始输出",
                "investment_conclusion": {"综合评级": "请查看下方原始输出", "核心逻辑": "请查看下方原始输出",
                                          "建议关注": "请查看下方原始输出"},
                "_raw_content": raw_result
            }

    except Exception as e:
        logging.error(f"调用AI API失败: {e}")
        return generate_mock_analysis(stock_text, expert_name)
