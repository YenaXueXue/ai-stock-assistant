import streamlit as st
import pandas as pd
import re
from data_fetcher import get_stock_info, format_stock_data_for_ai
from expert_skills import list_experts, load_skill
from ai_analyzer import analyze_with_expert

st.set_page_config(page_title="AI个股投研助手 - 专家模式", page_icon="📈", layout="wide")

st.title("📊 AI个股投研助手")
st.caption("基于 DeepSeek + 大师思维模型 的智能投研分析")

with st.sidebar:
    st.header("🧑‍🏫 选择分析专家")
    experts = list_experts()
    if not experts:
        st.error("未找到任何技能文件，请检查 skills/ 目录")
        st.stop()
    selected_expert = st.selectbox("请选择一位投资大师", experts)
    with st.expander("📖 查看该专家的分析框架"):
        try:
            skill_content = load_skill(selected_expert)
            st.markdown(skill_content[:500] + ("......" if len(skill_content) > 500 else ""))
        except Exception as e:
            st.error(f"加载技能失败: {e}")

col1, col2 = st.columns([3, 1])
with col1:
    symbol = st.text_input("请输入股票代码（6位数字）", placeholder="例如 000001 (平安银行)", value="000001")
with col2:
    st.write("")
    st.write("")
    analyze_btn = st.button("🚀 开始分析", type="primary", use_container_width=True)

if analyze_btn:
    if not symbol or not symbol.isdigit() or len(symbol) != 6:
        st.warning("⚠️ 请输入正确的6位数字股票代码")
    else:
        with st.spinner(f"📡 正在获取 {symbol} 的市场数据..."):
            stock_data = get_stock_info(symbol)

        if not stock_data.get('spot'):
            st.error("❌ 未找到该股票数据，请检查代码是否正确（仅支持A股）")
            st.stop()

        stock_text = format_stock_data_for_ai(stock_data)

        try:
            expert_skill = load_skill(selected_expert)
        except Exception as e:
            st.error(f"加载专家技能失败: {e}")
            st.stop()

        with st.spinner(f"🧠 {selected_expert} 正在深度分析中..."):
            analysis_result = analyze_with_expert(stock_text, expert_skill)

        st.divider()
        st.subheader(f"💡 {selected_expert} 的分析观点")

        # ===== 核心摘要 =====
        st.markdown("**📌 核心摘要**")
        st.info(analysis_result.get('summary', '暂无摘要'))

        # ===== 关键指标分析 =====
        st.markdown("**📊 关键指标分析**")
        key_metrics = analysis_result.get('key_metrics_analysis', {})
        metrics_config = [("估值", "估值"), ("成长性", "成长性"), ("财务健康", "财务健康"), ("技术面", "技术面")]
        cols = st.columns(2)
        for i, (label, key) in enumerate(metrics_config):
            value = key_metrics.get(key, '暂无数据')
            col = cols[i % 2]
            with col:
                st.markdown(f"""
                <div style='background-color: #f0f2f6; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; min-height: 80px;'>
                    <div style='font-weight: 600; font-size: 14px; color: #31333F; margin-bottom: 4px;'>{label}</div>
                    <div style='font-size: 14px; color: #262730; line-height: 1.6;'>{value}</div>
                </div>
                """, unsafe_allow_html=True)

        # ===== 财务数据一览表 =====
        st.markdown("---")
        st.markdown("### 📊 财务数据一览表")

        valuation = stock_data.get('valuation', {})


        def fmt_num(v, decimals=2):
            if v is None or v == '':
                return "--"
            try:
                return f"{float(v):.{decimals}f}"
            except:
                return str(v)


        pe_val = valuation.get('pe')
        pb_val = valuation.get('pb')
        roe_val = valuation.get('roe')
        turnover_val = valuation.get('turnover')
        close_val = valuation.get('close')
        change_pct = valuation.get('change_pct')

        valuation_df = pd.DataFrame({
            "指标": ["最新价", "涨跌幅", "市盈率 (PE)", "市净率 (PB)", "ROE (估算)", "换手率"],
            "当前值": [
                fmt_num(close_val, 2),
                f"{fmt_num(change_pct, 2)}%" if change_pct is not None else "--",
                fmt_num(pe_val, 2),
                fmt_num(pb_val, 2),
                f"{fmt_num(roe_val, 2)}%" if roe_val is not None else "--",
                f"{fmt_num(turnover_val, 2)}%" if turnover_val is not None else "--"
            ],
            "评价": [
                "实时数据",
                "反映短期走势",
                "需结合历史分位判断",
                "需结合历史分位判断",
                "仅供参考（估算值）",
                "反映交易活跃度"
            ]
        })

        st.dataframe(
            valuation_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "指标": st.column_config.TextColumn("指标", width="small"),
                "当前值": st.column_config.TextColumn("当前值", width="small"),
                "评价": st.column_config.TextColumn("评价", width="large"),
            }
        )

        # ===== 风险与机会矩阵（修复：从 risk_analysis 提取数据） =====
        st.markdown("#### ⚖️ 风险与机会矩阵")

        # 从 risk_analysis 中提取文本
        risk_analysis = analysis_result.get('risk_analysis', {})
        if isinstance(risk_analysis, dict):
            risk_text = "；".join([f"{k}：{v}" for k, v in risk_analysis.items() if v and v != "--"])
        else:
            risk_text = str(risk_analysis) if risk_analysis else "暂无风险分析"

        opportunities_text = analysis_result.get('opportunities', '暂无')

        matrix_df = pd.DataFrame({
            "维度": ["风险因素", "潜在机会"],
            "详情": [
                risk_text[:300] + "..." if len(str(risk_text)) > 300 else risk_text,
                str(opportunities_text)[:300] + "..." if len(str(opportunities_text)) > 300 else str(opportunities_text)
            ]
        })
        st.table(matrix_df)

        # ===== 行业对比 =====
        st.markdown("---")
        st.markdown("**🏭 行业对比**")
        st.write(analysis_result.get('industry_comparison', '暂无行业对比'))

        # ===== 分层风险分析 =====
        st.markdown("**⚠️ 详细风险分析**")
        risk = analysis_result.get('risk_analysis', {})
        if risk and isinstance(risk, dict):
            st.warning(f"**公司层面**：{risk.get('公司层面', '--')}")
            st.warning(f"**行业层面**：{risk.get('行业层面', '--')}")
            st.warning(f"**市场层面**：{risk.get('市场层面', '--')}")
        else:
            st.warning("暂无详细风险分析")

        # ===== 潜在机会 =====
        st.markdown("**🚀 潜在机会（详细）**")
        st.write(analysis_result.get('opportunities', '暂无'))

        # ===== 投资结论 =====
        st.markdown("**🎯 投资结论**")
        conclusion = analysis_result.get('investment_conclusion', {})
        if conclusion and isinstance(conclusion, dict):
            st.success(f"**综合评级**：{conclusion.get('综合评级', '--')}")
            st.info(f"**核心逻辑**：{conclusion.get('核心逻辑', '--')}")
            st.caption(f"**建议关注**：{conclusion.get('建议关注', '--')}")

        # ===== 原始数据展示 =====
        with st.expander("📄 查看原始数据（供参考）"):
            st.text(stock_text)

        with st.expander("🤖 查看 AI 原始返回内容（调试用）"):
            if "_raw_content" in analysis_result:
                st.text(analysis_result["_raw_content"])
            else:
                st.json(analysis_result)

st.divider()
st.caption("⚠️ 本工具仅供学习研究参考，不构成任何投资建议。")

# streamlit run app.py

