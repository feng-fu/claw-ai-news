#!/usr/bin/env python3
"""
AI News Fetcher
从多个来源获取AI相关新闻：ArXiv、Hacker News、AI公司博客、Google News
"""

import os
import re
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import feedparser
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AI相关关键词过滤列表
AI_KEYWORDS = [
    'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
    'neural', 'llm', 'large language model', 'gpt', 'claude', 'gemini',
    'openai', 'anthropic', 'google deepmind', 'meta ai', 'mistral',
    'transformer', 'model', 'training', 'inference', 'model',
    'chatgpt', 'copilot', 'bard', 'claude', 'pytorch', 'tensorflow',
    'nvidia', 'amd', 'intel', 'tpu', 'gpu', 'cluster', 'datacenter',
    'agent', 'rag', 'embedding', 'token', 'prompt', 'fine-tune',
    'multimodal', 'vision', 'speech', 'text-to-image', 'diffusion',
    'sora', 'video generation', 'image generation', 'stable diffusion',
    'autonomous', 'robotics', 'robot', 'self-driving', '自动驾驶',
    'anthropic', 'openai', 'google ai', 'meta ai', 'microsoft ai',
    'aws ai', 'amazon ai', 'nvidia ai', 'xai', 'mistral ai',
    'hugging face', 'replicate', 'runway', 'midjourney', ' DALLE',
    'sam', 'segment anything', 'yolo', 'clip', 'flamingo',
    'whisper', 'text-to-speech', 'tts', 'asr', 'speech-to-text',
    'benchmark', 'eval', 'training data', 'synthetic data',
    'alignment', 'rlhf', 'dpo', 'constitutional ai', 'safety',
    'regulation', 'policy', 'china ai', 'eu ai act', 'ai safety',
    'research', 'paper', 'arxiv', 'icml', 'neurips', 'cvpr',
    'startup', 'funding', 'acquisition', 'ipo', 'valuation',
    'api', 'sdk', 'developer', 'platform', 'cloud', 'azure',
    'serverless', 'edge', 'deployment', 'optimization', 'quantize',
    'moe', 'mixture of experts', 'routing', 'distillation',
    'context window', 'long context', '1m token', '128k',
    'tokenizer', 'vocabulary', 'architecture', 'attention',
    'mamba', 'state space', 'ssm', 'linear attention'
]

# 排除的非AI关键词
EXCLUDE_KEYWORDS = [
    'baseball', 'basketball', 'football', 'sports', 'nba', 'nfl',
    'weather', 'stock market', 'real estate', 'cooking', 'recipe',
    'travel', 'fashion', 'beauty', 'music', 'movie', 'film',
    'celebrity', 'gossip', 'politics', 'election', 'war',
    'bitcoin', 'crypto', 'cryptocurrency', 'blockchain',
    'gaming', 'video game', 'esports', 'playstation', 'xbox',
    'mobile', 'iphone', 'android', 'samsung', 'apple',
    'tv', 'netflix', 'streaming', 'hulu', 'disney+',
    'nutrition', 'health', 'fitness', 'diet', 'weight loss'
]

@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    url: str
    source: str
    published: str
    summary: str
    category: str  # categories like: model_product, infrastructure, dev生态, regulation, research
    importance: int  # 1-5, 5 is most important
    raw_data: dict

    def to_dict(self):
        return asdict(self)

class NewsFetcher:
    """新闻获取器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch(self) -> List[NewsItem]:
        raise NotImplementedError
    
    def is_ai_related(self, text: str) -> bool:
        """判断文本是否与AI相关"""
        text_lower = text.lower()
        
        # 先检查是否包含AI关键词
        has_ai_keyword = any(kw in text_lower for kw in AI_KEYWORDS)
        if not has_ai_keyword:
            return False
        
        # 检查是否包含排除关键词
        has_exclude = any(kw in text_lower for kw in EXCLUDE_KEYWORDS)
        if has_exclude:
            # 如果同时有AI关键词和排除关键词，看AI关键词是否更突出
            ai_count = sum(1 for kw in AI_KEYWORDS if kw in text_lower)
            exclude_count = sum(1 for kw in EXCLUDE_KEYWORDS if kw in text_lower)
            return ai_count > exclude_count
        
        return True
    
    def extract_category(self, text: str) -> str:
        """提取新闻分类"""
        text_lower = text.lower()
        
        # 模型与产品
        if any(k in text_lower for k in ['gpt', 'claude', 'gemini', 'model', 'product', 'release', 'launch', 'announce', 'new version', 'upgrade', 'api']):
            return 'model_product'
        
        # 算力与基础设施
        if any(k in text_lower for k in ['nvidia', 'amd', 'intel', 'gpu', 'tpu', 'chip', 'cloud', 'datacenter', 'cluster', 'inference', 'training', 'hardware']):
            return 'infrastructure'
        
        # 开发者生态
        if any(k in text_lower for k in ['developer', 'sdk', 'api', 'tool', 'framework', 'open source', 'github', 'hugging face', 'platform', 'agent', 'plugin']):
            return 'dev_ecosystem'
        
        # 监管与政策
        if any(k in text_lower for k in ['regulation', 'policy', 'law', 'government', 'china', 'eu', 'usa', 'safety', 'ban', 'restrict', 'act']):
            return 'regulation'
        
        # 科研
        if any(k in text_lower for k in ['research', 'paper', 'arxiv', 'study', 'experiment', 'benchmark', 'icml', 'neurips', 'cvpr']):
            return 'research'
        
        # 融资与商业化
        if any(k in text_lower for k in ['funding', 'investment', 'valuation', 'acquisition', 'ipo', 'revenue', 'startup', 'series', 'round']):
            return 'business'
        
        # 多模态与机器人
        if any(k in text_lower for k in ['robot', 'multimodal', 'vision', 'video', 'image generation', 'speech', 'voice', 'autonomous', 'drone']):
            return 'multimodal_robotics'
        
        return 'general'


class ArxivFetcher(NewsFetcher):
    """从ArXiv获取AI论文"""
    
    CATEGORIES = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV', 'cs.NE', 'stat.ML']
    
    def __init__(self):
        super().__init__('ArXiv')
        self.base_url = 'http://export.arxiv.org/api/query'
    
    def fetch(self) -> List[NewsItem]:
        items = []
        yesterday = datetime.now() - timedelta(days=7)  # 获取最近7天的论文
        
        for cat in self.CATEGORIES:
            try:
                params = {
                    'search_query': f'cat:{cat}',
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending',
                    'max_results': 20
                }
                
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'xml')
                entries = soup.find_all('entry')
                
                for entry in entries:
                    try:
                        published = datetime.strptime(entry.find('published').text[:10], '%Y-%m-%d')
                        if published < yesterday:
                            continue
                        
                        title = entry.find('title').text.replace('\n', ' ')
                        summary = entry.find('summary').text.replace('\n', ' ')[:300]
                        url = entry.find('id').text
                        
                        # ArXiv论文默认都是AI相关的
                        category = self.extract_category(title + ' ' + summary)
                        
                        item = NewsItem(
                            title=title,
                            url=url,
                            source='ArXiv',
                            published=entry.find('published').text[:10],
                            summary=summary,
                            category=category,
                            importance=3,
                            raw_data={'authors': [a.text for a in entry.find_all('author')]}
                        )
                        items.append(item)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing ArXiv entry: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error fetching ArXiv {cat}: {e}")
                continue
        
        logger.info(f"Fetched {len(items)} papers from ArXiv")
        return items


class HackerNewsFetcher(NewsFetcher):
    """从Hacker News获取AI讨论"""
    
    def __init__(self):
        super().__init__('HackerNews')
        self.base_url = 'https://hn.algolia.com/api/v1/search_by_date'
    
    def fetch(self) -> List[NewsItem]:
        items = []
        
        try:
            # 获取最近2天的AI相关Stories
            params = {
                'query': 'AI OR artificial intelligence OR machine learning OR LLM OR GPT OR neural network',
                'tags': 'story',
                'hitsPerPage': 50,
                'dateEnd': datetime.now().isoformat(),
                'dateStart': (datetime.now() - timedelta(days=2)).isoformat()
            }
            
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for hit in data.get('hits', []):
                try:
                    title = hit.get('title', '')
                    if not title or not self.is_ai_related(title):
                        continue
                    
                    url = hit.get('url', f"https://news.ycombinator.com/item?id={hit.get('objectID')}")
                    
                    item = NewsItem(
                        title=title,
                        url=url,
                        source='Hacker News',
                        published=hit.get('created_at', '')[:10],
                        summary=hit.get('story_text', '')[:200] if hit.get('story_text') else f"Points: {hit.get('points', 0)}",
                        category=self.extract_category(title),
                        importance=min(5, int(hit.get('points', 0) / 20) + 1),
                        raw_data={'points': hit.get('points', 0), 'author': hit.get('author')}
                    )
                    items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Error parsing HN entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching Hacker News: {e}")
        
        # 尝试RSS方式获取
        try:
            rss_url = 'https://hnrss.org/newest?q=AI'
            response = self.session.get(rss_url, timeout=30)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:20]:
                    title = entry.get('title', '')
                    if self.is_ai_related(title):
                        item = NewsItem(
                            title=title,
                            url=entry.get('link', ''),
                            source='Hacker News',
                            published=entry.get('published', '')[:10],
                            summary=entry.get('summary', '')[:200],
                            category=self.extract_category(title),
                            importance=3,
                            raw_data={}
                        )
                        # 避免重复
                        if not any(i.title == item.title for i in items):
                            items.append(item)
        except Exception as e:
            logger.warning(f"Error fetching HN RSS: {e}")
        
        logger.info(f"Fetched {len(items)} items from Hacker News")
        return items


class GoogleNewsFetcher(NewsFetcher):
    """从Google News获取AI新闻"""
    
    def __init__(self):
        super().__init__('Google News')
    
    def fetch(self) -> List[NewsItem]:
        items = []
        
        # 使用Google News RSS源
        rss_urls = [
            'https://news.google.com/rss/search?q=AI%20artificial%20intelligence&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=machine%20learning%20LLM&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=OpenAI%20Anthropic%20Google%20AI&hl=en-US&gl=US&ceid=US:en',
        ]
        
        for rss_url in rss_urls:
            try:
                response = self.session.get(rss_url, timeout=30)
                if response.status_code != 200:
                    continue
                    
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:30]:
                    try:
                        title = entry.get('title', '')
                        # 过滤掉非AI新闻
                        if not self.is_ai_related(title):
                            continue
                        
                        # 提取URL
                        url = entry.get('link', '')
                        if url.startswith('http'):
                            # Google News重定向URL，需要解析
                            if 'news.google.com' in url:
                                continue  # 跳过Google News自己的链接
                        
                        published = entry.get('published', '')
                        if published:
                            try:
                                published = datetime.strptime(published[:25], '%a, %d %b %Y %H:%M:%S').strftime('%Y-%m-%d')
                            except:
                                published = ''
                        
                        summary = entry.get('summary', '')[:200] if entry.get('summary') else ''
                        
                        item = NewsItem(
                            title=title,
                            url=url,
                            source='Google News',
                            published=published,
                            summary=summary,
                            category=self.extract_category(title),
                            importance=3,
                            raw_data={}
                        )
                        items.append(item)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing Google News entry: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error fetching Google News RSS: {e}")
                continue
        
        # 去重
        seen = set()
        unique_items = []
        for item in items:
            if item.title not in seen:
                seen.add(item.title)
                unique_items.append(item)
        
        logger.info(f"Fetched {len(unique_items)} items from Google News")
        return unique_items


class AIBlogFetcher(NewsFetcher):
    """从AI公司博客获取更新"""
    
    BLOGS = {
        'OpenAI': [
            'https://openai.com/blog',
            'https://openai.com/research'
        ],
        'Anthropic': [
            'https://www.anthropic.com/news',
            'https://www.anthropic.com/research'
        ],
        'Google AI': [
            'https://blog.google/technology/ai/',
            'https://research.google/blog/'
        ],
        'Meta AI': [
            'https://ai.meta.com/blog/',
            'https://research.meta.com/'
        ],
        'Microsoft': [
            'https://blogs.microsoft.com/ai/',
            'https://azure.microsoft.com/blog/topics/artificial-intelligence/'
        ],
        'AWS': [
            'https://aws.amazon.com/blogs/machine-learning/',
            'https://aws.amazon.com/blogs/ai/'
        ],
        'NVIDIA': [
            'https://blogs.nvidia.com/category/ai/',
            'https://newsroom.nvidia.com/tag/ai/'
        ],
        'Hugging Face': [
            'https://huggingface.co/blog'
        ],
        'Mistral AI': [
            'https://mistral.ai/news/'
        ],
        'xAI': [
            'https://x.ai/blog'
        ]
    }
    
    def __init__(self):
        super().__init__('AI Blogs')
    
    def fetch(self) -> List[NewsItem]:
        items = []
        
        def fetch_blog(company: str, url: str) -> List[NewsItem]:
            blog_items = []
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    return blog_items
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 尝试找RSS
                rss_link = soup.find('link', type='application/rss+xml')
                if rss_link:
                    rss_url = rss_link.get('href')
                    if not rss_url.startswith('http'):
                        rss_url = urllib.parse.urljoin(url, rss_url)
                    return self._fetch_rss(company, rss_url)
                
                # 尝试找文章链接
                articles = soup.find_all('a', href=True)
                for a in articles:
                    href = a.get('href', '')
                    text = a.get_text(strip=True)
                    
                    # 过滤文章链接
                    if len(text) > 20 and any(kw in href.lower() for kw in ['/blog/', '/news/', '/research/', '/post/', '/article']):
                        if not href.startswith('http'):
                            href = urllib.parse.urljoin(url, href)
                        
                        if self.is_ai_related(text):
                            item = NewsItem(
                                title=text[:150],
                                url=href,
                                source=company,
                                published=datetime.now().strftime('%Y-%m-%d'),
                                summary=f"Article from {company} blog",
                                category=self.extract_category(text),
                                importance=4,
                                raw_data={}
                            )
                            blog_items.append(item)
                            
            except Exception as e:
                logger.warning(f"Error fetching {company} blog: {e}")
            return blog_items
        
        # 并行获取所有博客
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for company, urls in self.BLOGS.items():
                for url in urls:
                    futures.append((company, url, executor.submit(fetch_blog, company, url)))
            
            for company, url, future in futures:
                try:
                    blog_items = future.result()
                    items.extend(blog_items)
                except Exception as e:
                    logger.warning(f"Error in blog future: {e}")
        
        # 去重
        seen = set()
        unique_items = []
        for item in items:
            if item.title not in seen:
                seen.add(item.title)
                unique_items.append(item)
        
        logger.info(f"Fetched {len(unique_items)} items from AI blogs")
        return unique_items
    
    def _fetch_rss(self, company: str, url: str) -> List[NewsItem]:
        items = []
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return items
            
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:10]:
                title = entry.get('title', '')
                if not self.is_ai_related(title):
                    continue
                
                item = NewsItem(
                    title=title[:150],
                    url=entry.get('link', ''),
                    source=company,
                    published=entry.get('published', '')[:10] if entry.get('published') else datetime.now().strftime('%Y-%m-%d'),
                    summary=entry.get('summary', '')[:200] if entry.get('summary') else '',
                    category=self.extract_category(title),
                    importance=4,
                    raw_data={}
                )
                items.append(item)
                
        except Exception as e:
            logger.warning(f"Error fetching RSS for {company}: {e}")
        
        return items


class NewsAggregator:
    """新闻聚合器"""
    
    def __init__(self):
        self.fetchers = [
            ArxivFetcher(),
            HackerNewsFetcher(),
            GoogleNewsFetcher(),
            AIBlogFetcher()
        ]
    
    def fetch_all(self) -> List[NewsItem]:
        """获取所有来源的新闻"""
        all_news = []
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(f.fetch): f for f in self.fetchers}
            
            for future in as_completed(futures):
                fetcher = futures[future]
                try:
                    items = future.result()
                    all_news.extend(items)
                    logger.info(f"Fetched {len(items)} from {fetcher.name}")
                except Exception as e:
                    logger.error(f"Error fetching from {fetcher.name}: {e}")
        
        # 按重要性排序
        all_news.sort(key=lambda x: x.importance, reverse=True)
        
        # 去重（基于标题相似度）
        unique_news = self._deduplicate(all_news)
        
        logger.info(f"Total unique news: {len(unique_news)}")
        return unique_news
    
    def _deduplicate(self, items: List[NewsItem]) -> List[NewsItem]:
        """基于标题相似度去重"""
        seen = set()
        unique = []
        
        for item in items:
            # 简单去重：标准化标题后比较
            normalized = re.sub(r'[^a-z0-9]', '', item.title.lower())
            if normalized not in seen and len(normalized) > 10:
                seen.add(normalized)
                unique.append(item)
        
        return unique


def save_news(news: List[NewsItem], filepath: str = 'news_cache.json'):
    """保存新闻到文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([n.to_dict() for n in news], f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(news)} news items to {filepath}")


def load_news(filepath: str = 'news_cache.json') -> List[NewsItem]:
    """从文件加载新闻"""
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return [NewsItem(**item) for item in data]


def main():
    """主函数"""
    logger.info("Starting news fetch...")
    
    aggregator = NewsAggregator()
    news = aggregator.fetch_all()
    
    # 保存到缓存文件
    save_news(news)
    
    # 打印统计
    categories = {}
    for item in news:
        categories[item.category] = categories.get(item.category, 0) + 1
    
    logger.info(f"News by category: {categories}")
    logger.info(f"Total news: {len(news)}")


if __name__ == '__main__':
    main()
