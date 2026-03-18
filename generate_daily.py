#!/usr/bin/env python3
"""
AI Daily Report Generator
生成AI日报，按照科技周刊格式输出Markdown
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 尝试导入NewsItem，如果失败则定义
try:
    from fetch_news import NewsItem, load_news, save_news, NewsAggregator
except ImportError:
    # 如果fetch_news未定义NewsItem，在这里定义
    from dataclasses import dataclass
    
    @dataclass
    class NewsItem:
        title: str
        url: str
        source: str
        published: str
        summary: str
        category: str
        importance: int
        raw_data: dict
        
        def to_dict(self):
            return {
                'title': self.title,
                'url': self.url,
                'source': self.source,
                'published': self.published,
                'summary': self.summary,
                'category': self.category,
                'importance': self.importance,
                'raw_data': self.raw_data
            }
    
    def load_news(filepath: str = 'news_cache.json') -> List[NewsItem]:
        if not os.path.exists(filepath):
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [NewsItem(**item) for item in data]


class DailyReportGenerator:
    """日报生成器"""
    
    CATEGORY_NAMES = {
        'model_product': '🧠 模型与产品',
        'infrastructure': '⚡ 算力与基础设施',
        'dev_ecosystem': '🛠️ 开发者生态',
        'regulation': '📜 监管与政策',
        'research': '🔬 科研进展',
        'business': '💰 商业与融资',
        'multimodal_robotics': '🤖 多模态与机器人',
        'general': '📰 综合'
    }
    
    def __init__(self, news: List[NewsItem]):
        self.news = news
        self.today = datetime.now().strftime('%Y-%m-%d')
        
    def generate_cover_theme(self) -> str:
        """生成封面主题 - 一句话概括今日重点"""
        if not self.news:
            return "今日AI领域暂无重要更新"
        
        # 找出最重要的一些新闻
        top_news = sorted(self.news, key=lambda x: x.importance, reverse=True)[:10]
        
        # 按类别统计
        category_count = defaultdict(int)
        for n in top_news:
            category_count[n.category] += 1
        
        # 找出最热的类别
        if category_count:
            top_category = max(category_count.items(), key=lambda x: x[1])[0]
            category_name = self.CATEGORY_NAMES.get(top_category, top_category)
            
            # 生成封面主题
            themes = {
                'model_product': f"模型迭代加速：{len([n for n in top_news if n.category == 'model_product'])}个模型/产品更新发布",
                'infrastructure': f"算力竞赛升温：{len([n for n in top_news if n.category == 'infrastructure'])}条硬件/基础设施动态",
                'dev_ecosystem': f"开发者工具爆发：{len([n for n in top_news if n.category == 'dev_ecosystem'])}个开发工具/平台更新",
                'regulation': f"监管关注持续：{len([n for n in top_news if n.category == 'regulation'])}条政策法规动态",
                'research': f"学术研究活跃：{len([n for n in top_news if n.category == 'research'])}篇重要论文发布",
                'business': f"商业化进程加快：{len([n for n in top_news if n.category == 'business'])}条融资/商业化进展",
                'multimodal_robotics': f"多模态与机器人技术突破：{len([n for n in top_news if n.category == 'multimodal_robotics'])}条最新进展"
            }
            
            return themes.get(top_category, f"今日AI领域共{len(self.news)}条更新")
        
        return f"今日AI领域共{len(self.news)}条更新"
    
    def generate_highlights(self, count: int = 8) -> str:
        """生成重点新闻（5-8条详细分析）"""
        highlights = sorted(self.news, key=lambda x: x.importance, reverse=True)[:count]
        
        output = []
        output.append("## 🌟 重点新闻\n")
        
        for i, item in enumerate(highlights, 1):
            # 生成简要分析
            analysis = self._generate_analysis(item)
            
            output.append(f"### {i}. {item.title}")
            output.append(f"**来源**: {item.source} | **日期**: {item.published}")
            output.append(f"**分类**: {self.CATEGORY_NAMES.get(item.category, item.category)}")
            output.append(f"\n{item.summary}")
            output.append(f"\n**点评**: {analysis}")
            output.append(f"\n[阅读原文]({item.url})")
            output.append("\n---\n")
        
        return "\n".join(output)
    
    def _generate_analysis(self, item: NewsItem) -> str:
        """为新闻生成简要分析/观点"""
        title_lower = item.title.lower()
        
        # 基于标题和分类生成分析
        if 'gpt' in title_lower or 'claude' in title_lower or 'gemini' in title_lower:
            return "头部模型持续迭代，性能提升明显，展现出大模型竞争的激烈程度。"
        elif 'openai' in title_lower or 'anthropic' in title_lower:
            return "头部AI公司持续引领行业发展，新产品新功能值得关注。"
        elif 'nvidia' in title_lower or 'gpu' in title_lower or 'chip' in title_lower:
            return "算力需求持续旺盛，硬件更新换代加速，AI基础设施竞争加剧。"
        elif 'arxiv' in title_lower or 'paper' in title_lower or 'research' in title_lower:
            return "学术研究持续推进，新方法和新技术值得关注。"
        elif 'regulation' in title_lower or 'policy' in title_lower or 'law' in title_lower:
            return "监管政策对AI发展影响重大，需要持续关注。"
        elif 'funding' in title_lower or 'valuation' in title_lower or 'acquisition' in title_lower:
            return "AI领域资本活跃，商业化进程加快。"
        elif 'developer' in title_lower or 'sdk' in title_lower or 'tool' in title_lower:
            return "开发者工具生态完善，有助于降低AI应用门槛。"
        elif 'robot' in title_lower or 'autonomous' in title_lower:
            return "机器人技术进展显著，落地应用前景广阔。"
        else:
            return "AI领域重要动态，值得关注。"
    
    def generate_categories(self) -> str:
        """生成分类板块"""
        # 按类别分组
        categories = defaultdict(list)
        for item in self.news:
            categories[item.category].append(item)
        
        output = []
        output.append("## 📊 分类板块\n")
        
        # 优先显示的类别顺序
        category_order = ['model_product', 'infrastructure', 'dev_ecosystem', 'research', 'business', 'multimodal_robotics', 'regulation', 'general']
        
        for cat in category_order:
            if cat not in categories or not categories[cat]:
                continue
            
            items = categories[cat][:8]  # 每类最多8条
            output.append(f"### {self.CATEGORY_NAMES.get(cat, cat)}\n")
            
            for item in items:
                output.append(f"- [{item.title}]({item.url}) ({item.source})")
            
            output.append("")
        
        return "\n".join(output)
    
    def generate_tools(self) -> str:
        """生成工具/资源推荐"""
        tools = [
            ("🤗 Hugging Face", "https://huggingface.co", "最大的开源模型库"),
            ("🧪 LM Studio", "https://lmstudio.ai", "本地运行LLM的桌面应用"),
            ("📚 ArXiv", "https://arxiv.org", "最新AI论文"),
            ("🔍 Perplexity", "https://www.perplexity.ai", "AI驱动的搜索引擎"),
            ("📊 MLPerf", "https://mlperf.org", "AI性能基准测试"),
            ("🐙 GitHub Trending", "https://github.com/trending?since=weekly", "热门开源项目"),
        ]
        
        output = []
        output.append("## 🛠️ 工具/资源推荐\n")
        
        for name, url, desc in tools:
            output.append(f"- [{name}]({url}): {desc}")
        
        output.append("")
        return "\n".join(output)
    
    def generate_footer(self) -> str:
        """生成页脚"""
        return f"""
---
*本日报由AI自动生成，每日UTC 0:00更新*

**数据来源**: ArXiv, Hacker News, Google News, AI公司博客

**关注我们**: [GitHub](https://github.com/feng-fu/claw-ai-news) | [Issues](https://github.com/feng-fu/claw-ai-news/issues)

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    def generate(self) -> str:
        """生成完整日报"""
        # 封面
        cover = f"""---
layout: daily
title: AI Daily Report - {self.today}
date: {self.today}
---

# 🤖 AI Daily Report

## 📌 {self.generate_cover_theme()}

*日期: {self.today}*

"""
        
        # 重点新闻
        highlights = self.generate_highlights(8)
        
        # 分类板块
        categories = self.generate_categories()
        
        # 工具推荐
        tools = self.generate_tools()
        
        # 页脚
        footer = self.generate_footer()
        
        return cover + highlights + "\n" + categories + "\n" + tools + "\n" + footer


def main():
    """主函数"""
    logger.info("Generating daily report...")
    
    # 加载新闻
    news = load_news()
    
    if not news:
        logger.warning("No news loaded, fetching fresh news...")
        try:
            aggregator = NewsAggregator()
            news = aggregator.fetch_all()
            save_news(news)
        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")
            # 如果没有新闻，生成一个示例
            news = []
    
    # 生成日报
    generator = DailyReportGenerator(news)
    report = generator.generate()
    
    # 保存日报
    output_path = os.path.join('daily', f'{datetime.now().strftime("%Y-%m-%d")}.md')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Daily report saved to {output_path}")
    
    # 同时更新 index.md
    index_path = 'index.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Index updated to {index_path}")
    
    print(f"\n=== Daily Report Preview ===\n")
    print(report[:2000])
    print("\n... (truncated) ...")


if __name__ == '__main__':
    main()
