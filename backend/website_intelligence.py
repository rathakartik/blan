"""
Website Intelligence Engine
Comprehensive ROI-focused website crawling and analysis system
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from typing import Dict, List, Set, Optional, Any, Tuple
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import textstat
import logging
from dataclasses import dataclass, asdict
import hashlib
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

logger = logging.getLogger(__name__)

@dataclass
class PageData:
    """Represents analyzed data for a single webpage"""
    url: str
    title: str
    description: str
    content: str
    word_count: int
    reading_level: float
    sentiment_score: float
    keywords: List[str]
    internal_links: List[str]
    external_links: List[str]
    images: List[Dict[str, str]]
    forms: List[Dict[str, Any]]
    contact_info: Dict[str, List[str]]
    navigation_elements: List[str]
    conversion_elements: List[Dict[str, str]]
    last_crawled: datetime
    content_hash: str
    page_type: str
    intent_categories: List[str]
    user_journey_stage: str
    seo_score: float
    accessibility_score: float

@dataclass
class SiteStructure:
    """Represents the complete website structure and intelligence"""
    domain: str
    total_pages: int
    page_hierarchy: Dict[str, List[str]]
    navigation_paths: Dict[str, List[str]]
    conversion_funnels: List[List[str]]
    content_categories: Dict[str, List[str]]
    intent_mapping: Dict[str, List[str]]
    user_journey_flows: Dict[str, List[str]]
    site_map: Dict[str, PageData]
    crawl_depth: int
    last_full_crawl: datetime
    roi_metrics: Dict[str, Any]

@dataclass
class UserIntent:
    """Represents user intent analysis"""
    intent_type: str
    confidence: float
    suggested_pages: List[str]
    conversion_probability: float
    recommended_actions: List[str]
    journey_stage: str

@dataclass
class ROIMetrics:
    """ROI tracking metrics"""
    page_views: int
    time_on_page: float
    bounce_rate: float
    conversion_rate: float
    lead_generation: int
    support_ticket_reduction: int
    user_satisfaction: float
    navigation_efficiency: float
    content_effectiveness: float

class WebsiteIntelligenceEngine:
    """Main engine for website crawling, analysis, and intelligence"""
    
    def __init__(self, db_service=None):
        self.db_service = db_service
        self.session = None
        self.stop_words = set(stopwords.words('english'))
        
        # Intent classification patterns
        self.intent_patterns = {
            'product_inquiry': [
                'product', 'service', 'buy', 'purchase', 'price', 'cost', 'features',
                'specs', 'specifications', 'compare', 'review', 'demo'
            ],
            'support': [
                'help', 'support', 'problem', 'issue', 'error', 'trouble', 'fix',
                'how to', 'tutorial', 'guide', 'faq', 'documentation'
            ],
            'navigation': [
                'find', 'where', 'locate', 'navigate', 'search', 'looking for',
                'page', 'section', 'menu', 'link'
            ],
            'contact': [
                'contact', 'phone', 'email', 'address', 'location', 'office',
                'support', 'sales', 'team', 'representative'
            ],
            'information': [
                'about', 'company', 'history', 'team', 'mission', 'vision',
                'values', 'news', 'blog', 'resources'
            ],
            'conversion': [
                'sign up', 'register', 'subscribe', 'download', 'free trial',
                'get started', 'book', 'schedule', 'appointment', 'quote'
            ]
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AI Voice Assistant Website Intelligence Bot/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def crawl_website(self, domain: str, max_pages: int = 100, max_depth: int = 3) -> SiteStructure:
        """
        Crawl and analyze entire website
        """
        logger.info(f"Starting website crawl for {domain}")
        
        crawled_urls: Set[str] = set()
        to_crawl: List[Tuple[str, int]] = [(f"https://{domain}", 0)]
        site_map: Dict[str, PageData] = {}
        
        while to_crawl and len(crawled_urls) < max_pages:
            url, depth = to_crawl.pop(0)
            
            if url in crawled_urls or depth > max_depth:
                continue
                
            try:
                page_data = await self.analyze_page(url)
                if page_data:
                    site_map[url] = page_data
                    crawled_urls.add(url)
                    
                    # Add internal links to crawl queue
                    if depth < max_depth:
                        for link in page_data.internal_links:
                            if link not in crawled_urls:
                                to_crawl.append((link, depth + 1))
                                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue
        
        # Build site structure
        site_structure = await self.build_site_structure(domain, site_map)
        
        # Store in database
        if self.db_service:
            await self.store_site_structure(site_structure)
        
        logger.info(f"Completed crawl for {domain}: {len(site_map)} pages analyzed")
        return site_structure
    
    async def analyze_page(self, url: str) -> Optional[PageData]:
        """
        Analyze individual webpage for content, structure, and intelligence
        """
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')
                
                # Extract basic info
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""
                
                description = soup.find('meta', attrs={'name': 'description'})
                description_text = description.get('content', '') if description else ""
                
                # Extract main content
                content = self.extract_main_content(soup)
                word_count = len(content.split())
                
                # Content analysis
                reading_level = textstat.flesch_reading_ease(content) if content else 0
                sentiment_score = self.analyze_sentiment(content)
                keywords = self.extract_keywords(content)
                
                # Extract links
                internal_links, external_links = self.extract_links(soup, url)
                
                # Extract images
                images = self.extract_images(soup, url)
                
                # Extract forms
                forms = self.extract_forms(soup)
                
                # Extract contact information
                contact_info = self.extract_contact_info(content)
                
                # Extract navigation elements
                navigation_elements = self.extract_navigation(soup)
                
                # Extract conversion elements
                conversion_elements = self.extract_conversion_elements(soup)
                
                # Classify page type and intent
                page_type = self.classify_page_type(url, title_text, content)
                intent_categories = self.classify_content_intent(content)
                user_journey_stage = self.determine_journey_stage(page_type, content)
                
                # Calculate scores
                seo_score = self.calculate_seo_score(soup, content)
                accessibility_score = self.calculate_accessibility_score(soup)
                
                return PageData(
                    url=url,
                    title=title_text,
                    description=description_text,
                    content=content,
                    word_count=word_count,
                    reading_level=reading_level,
                    sentiment_score=sentiment_score,
                    keywords=keywords,
                    internal_links=internal_links,
                    external_links=external_links,
                    images=images,
                    forms=forms,
                    contact_info=contact_info,
                    navigation_elements=navigation_elements,
                    conversion_elements=conversion_elements,
                    last_crawled=datetime.utcnow(),
                    content_hash=hashlib.md5(content.encode()).hexdigest(),
                    page_type=page_type,
                    intent_categories=intent_categories,
                    user_journey_stage=user_journey_stage,
                    seo_score=seo_score,
                    accessibility_score=accessibility_score
                )
                
        except Exception as e:
            logger.error(f"Error analyzing page {url}: {e}")
            return None
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from webpage"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Try to find main content areas
        main_content = ""
        
        # Common content selectors
        content_selectors = [
            'main', 'article', '[role="main"]', 
            '.content', '.main-content', '.post-content',
            '#content', '#main', '#main-content'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                main_content = content_element.get_text()
                break
        
        # Fallback to body content
        if not main_content:
            main_content = soup.get_text()
        
        # Clean up content
        lines = (line.strip() for line in main_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        main_content = ' '.join(chunk for chunk in chunks if chunk)
        
        return main_content
    
    def analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis"""
        if not text:
            return 0.0
        
        positive_words = [
            'excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'good',
            'best', 'quality', 'professional', 'reliable', 'trusted', 'secure'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'poor', 'worst', 'problem', 'issue',
            'error', 'failed', 'broken', 'difficult', 'complicated'
        ]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        if total_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_words
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords using TF-IDF"""
        if not text:
            return []
        
        try:
            # Clean text
            words = word_tokenize(text.lower())
            words = [word for word in words if word.isalpha() and word not in self.stop_words]
            cleaned_text = ' '.join(words)
            
            if not cleaned_text:
                return []
            
            # Use TF-IDF
            vectorizer = TfidfVectorizer(max_features=max_keywords, ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform([cleaned_text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            keyword_scores = list(zip(feature_names, scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [keyword for keyword, score in keyword_scores if score > 0]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[str], List[str]]:
        """Extract internal and external links"""
        internal_links = []
        external_links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)
            
            if parsed_url.netloc == base_domain:
                internal_links.append(absolute_url)
            elif parsed_url.netloc:  # External link
                external_links.append(absolute_url)
        
        return internal_links, external_links
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract image information"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    'src': absolute_url,
                    'alt': alt,
                    'title': title
                })
        
        return images
    
    def extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract form information"""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get').lower(),
                'inputs': []
            }
            
            for input_elem in form.find_all(['input', 'textarea', 'select']):
                input_data = {
                    'type': input_elem.get('type', 'text'),
                    'name': input_elem.get('name', ''),
                    'placeholder': input_elem.get('placeholder', ''),
                    'required': input_elem.has_attr('required')
                }
                form_data['inputs'].append(input_data)
            
            forms.append(form_data)
        
        return forms
    
    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """Extract contact information from text"""
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': []
        }
        
        # Email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['emails'] = list(set(emails))
        
        # Phone regex (various formats)
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        contact_info['phones'] = list(set([''.join(phone) for phone in phones]))
        
        return contact_info
    
    def extract_navigation(self, soup: BeautifulSoup) -> List[str]:
        """Extract navigation elements"""
        nav_elements = []
        
        # Common navigation selectors
        nav_selectors = ['nav', '.nav', '.navbar', '.navigation', '.menu', '#menu']
        
        for selector in nav_selectors:
            nav_elem = soup.select(selector)
            for nav in nav_elem:
                links = nav.find_all('a')
                for link in links:
                    text = link.get_text().strip()
                    if text:
                        nav_elements.append(text)
        
        return list(set(nav_elements))
    
    def extract_conversion_elements(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract conversion-focused elements"""
        conversion_elements = []
        
        # CTA buttons
        cta_selectors = [
            'button', '.btn', '.button', '.cta', 
            'input[type="submit"]', '.call-to-action'
        ]
        
        for selector in cta_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                if text:
                    conversion_elements.append({
                        'type': 'button',
                        'text': text,
                        'element': elem.name
                    })
        
        return conversion_elements
    
    def classify_page_type(self, url: str, title: str, content: str) -> str:
        """Classify page type based on URL, title, and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Page type patterns
        if any(pattern in url_lower for pattern in ['/product', '/shop', '/buy']):
            return 'product'
        elif any(pattern in url_lower for pattern in ['/about', '/company']):
            return 'about'
        elif any(pattern in url_lower for pattern in ['/contact', '/support']):
            return 'contact'
        elif any(pattern in url_lower for pattern in ['/blog', '/news', '/article']):
            return 'content'
        elif any(pattern in url_lower for pattern in ['/service', '/solution']):
            return 'service'
        elif url_lower.endswith('/') or url_lower.endswith('index'):
            return 'homepage'
        else:
            return 'general'
    
    def classify_content_intent(self, content: str) -> List[str]:
        """Classify content by user intent categories"""
        content_lower = content.lower()
        intent_scores = {}
        
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return intents with scores above threshold
        threshold = 2
        return [intent for intent, score in intent_scores.items() if score >= threshold]
    
    def determine_journey_stage(self, page_type: str, content: str) -> str:
        """Determine user journey stage"""
        content_lower = content.lower()
        
        # Awareness stage indicators
        awareness_keywords = ['learn', 'discover', 'what is', 'introduction', 'overview']
        if any(keyword in content_lower for keyword in awareness_keywords) or page_type in ['content', 'about']:
            return 'awareness'
        
        # Consideration stage indicators
        consideration_keywords = ['compare', 'vs', 'features', 'benefits', 'pros and cons']
        if any(keyword in content_lower for keyword in consideration_keywords) or page_type == 'service':
            return 'consideration'
        
        # Decision stage indicators
        decision_keywords = ['buy', 'purchase', 'price', 'contact', 'demo', 'trial']
        if any(keyword in content_lower for keyword in decision_keywords) or page_type in ['product', 'contact']:
            return 'decision'
        
        return 'awareness'
    
    def calculate_seo_score(self, soup: BeautifulSoup, content: str) -> float:
        """Calculate basic SEO score"""
        score = 0.0
        max_score = 100.0
        
        # Title tag (20 points)
        title = soup.find('title')
        if title and title.get_text().strip():
            score += 20
        
        # Meta description (15 points)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            score += 15
        
        # H1 tag (15 points)
        h1 = soup.find('h1')
        if h1 and h1.get_text().strip():
            score += 15
        
        # Content length (20 points)
        if len(content.split()) >= 300:
            score += 20
        elif len(content.split()) >= 100:
            score += 10
        
        # Images with alt text (10 points)
        images = soup.find_all('img')
        if images:
            images_with_alt = [img for img in images if img.get('alt')]
            if len(images_with_alt) / len(images) >= 0.8:
                score += 10
        
        # Internal links (10 points)
        internal_links = len([link for link in soup.find_all('a', href=True) 
                             if not link['href'].startswith('http')])
        if internal_links >= 3:
            score += 10
        
        # Meta viewport (10 points)
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport:
            score += 10
        
        return min(score, max_score)
    
    def calculate_accessibility_score(self, soup: BeautifulSoup) -> float:
        """Calculate basic accessibility score"""
        score = 0.0
        max_score = 100.0
        
        # Alt text for images (30 points)
        images = soup.find_all('img')
        if images:
            images_with_alt = [img for img in images if img.get('alt')]
            alt_ratio = len(images_with_alt) / len(images)
            score += alt_ratio * 30
        else:
            score += 30  # No images to worry about
        
        # Form labels (25 points)
        inputs = soup.find_all('input')
        if inputs:
            labeled_inputs = []
            for input_elem in inputs:
                input_id = input_elem.get('id')
                if input_id:
                    label = soup.find('label', attrs={'for': input_id})
                    if label:
                        labeled_inputs.append(input_elem)
            
            if inputs:
                label_ratio = len(labeled_inputs) / len(inputs)
                score += label_ratio * 25
        else:
            score += 25  # No forms to worry about
        
        # Semantic HTML (20 points)
        semantic_tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        semantic_count = sum(1 for tag in semantic_tags if soup.find(tag))
        score += (semantic_count / len(semantic_tags)) * 20
        
        # Heading structure (15 points)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings:
            h1_count = len(soup.find_all('h1'))
            if h1_count == 1:  # Exactly one H1
                score += 15
            elif h1_count > 0:
                score += 10
        
        # Color contrast and focus indicators (10 points)
        # This is a simplified check - in reality, you'd need more complex analysis
        focus_elements = soup.find_all(['a', 'button', 'input', 'select', 'textarea'])
        if focus_elements:
            score += 10
        
        return min(score, max_score)
    
    async def build_site_structure(self, domain: str, site_map: Dict[str, PageData]) -> SiteStructure:
        """Build comprehensive site structure from crawled data"""
        
        # Build page hierarchy
        page_hierarchy = defaultdict(list)
        for url in site_map.keys():
            path_parts = urlparse(url).path.strip('/').split('/')
            if len(path_parts) > 1:
                parent = '/'.join(path_parts[:-1])
                page_hierarchy[parent].append(url)
        
        # Build navigation paths
        navigation_paths = {}
        for url, page_data in site_map.items():
            paths = []
            for link in page_data.internal_links:
                if link in site_map:
                    paths.append(link)
            navigation_paths[url] = paths
        
        # Identify conversion funnels
        conversion_funnels = self.identify_conversion_funnels(site_map)
        
        # Categorize content
        content_categories = self.categorize_content(site_map)
        
        # Build intent mapping
        intent_mapping = {}
        for url, page_data in site_map.items():
            for intent in page_data.intent_categories:
                if intent not in intent_mapping:
                    intent_mapping[intent] = []
                intent_mapping[intent].append(url)
        
        # Build user journey flows
        user_journey_flows = self.build_user_journey_flows(site_map)
        
        # Calculate ROI metrics
        roi_metrics = await self.calculate_roi_metrics(domain, site_map)
        
        return SiteStructure(
            domain=domain,
            total_pages=len(site_map),
            page_hierarchy=dict(page_hierarchy),
            navigation_paths=navigation_paths,
            conversion_funnels=conversion_funnels,
            content_categories=content_categories,
            intent_mapping=intent_mapping,
            user_journey_flows=user_journey_flows,
            site_map=site_map,
            crawl_depth=3,
            last_full_crawl=datetime.utcnow(),
            roi_metrics=roi_metrics
        )
    
    def identify_conversion_funnels(self, site_map: Dict[str, PageData]) -> List[List[str]]:
        """Identify potential conversion funnels"""
        funnels = []
        
        # Find pages by journey stage
        awareness_pages = [url for url, page in site_map.items() 
                          if page.user_journey_stage == 'awareness']
        consideration_pages = [url for url, page in site_map.items() 
                              if page.user_journey_stage == 'consideration']
        decision_pages = [url for url, page in site_map.items() 
                         if page.user_journey_stage == 'decision']
        
        # Create potential funnels
        for awareness in awareness_pages[:3]:  # Limit to top 3
            for consideration in consideration_pages[:2]:
                for decision in decision_pages[:2]:
                    funnel = [awareness, consideration, decision]
                    funnels.append(funnel)
        
        return funnels[:5]  # Return top 5 funnels
    
    def categorize_content(self, site_map: Dict[str, PageData]) -> Dict[str, List[str]]:
        """Categorize content by type and topic"""
        categories = defaultdict(list)
        
        for url, page_data in site_map.items():
            # Categorize by page type
            categories[page_data.page_type].append(url)
            
            # Categorize by intent
            for intent in page_data.intent_categories:
                categories[f"intent_{intent}"].append(url)
            
            # Categorize by journey stage
            categories[f"journey_{page_data.user_journey_stage}"].append(url)
        
        return dict(categories)
    
    def build_user_journey_flows(self, site_map: Dict[str, PageData]) -> Dict[str, List[str]]:
        """Build user journey flows based on page relationships"""
        flows = {
            'awareness_to_consideration': [],
            'consideration_to_decision': [],
            'support_flow': [],
            'product_discovery': []
        }
        
        # Simple flow building based on page types and intents
        for url, page_data in site_map.items():
            if page_data.page_type == 'homepage':
                flows['product_discovery'].append(url)
            elif 'product_inquiry' in page_data.intent_categories:
                flows['product_discovery'].append(url)
            elif 'support' in page_data.intent_categories:
                flows['support_flow'].append(url)
            elif page_data.user_journey_stage == 'awareness':
                flows['awareness_to_consideration'].append(url)
            elif page_data.user_journey_stage == 'decision':
                flows['consideration_to_decision'].append(url)
        
        return flows
    
    async def calculate_roi_metrics(self, domain: str, site_map: Dict[str, PageData]) -> Dict[str, Any]:
        """Calculate ROI metrics for the website"""
        
        total_pages = len(site_map)
        avg_seo_score = np.mean([page.seo_score for page in site_map.values()]) if site_map else 0
        avg_accessibility_score = np.mean([page.accessibility_score for page in site_map.values()]) if site_map else 0
        
        # Count conversion elements
        total_conversion_elements = sum(len(page.conversion_elements) for page in site_map.values())
        
        # Count forms (lead generation potential)
        total_forms = sum(len(page.forms) for page in site_map.values())
        
        # Calculate content quality
        avg_word_count = np.mean([page.word_count for page in site_map.values()]) if site_map else 0
        avg_reading_level = np.mean([page.reading_level for page in site_map.values()]) if site_map else 0
        
        # Intent coverage
        all_intents = set()
        for page in site_map.values():
            all_intents.update(page.intent_categories)
        intent_coverage = len(all_intents)
        
        return {
            'total_pages_analyzed': total_pages,
            'avg_seo_score': float(avg_seo_score),
            'avg_accessibility_score': float(avg_accessibility_score),
            'total_conversion_elements': total_conversion_elements,
            'lead_generation_potential': total_forms,
            'avg_content_length': float(avg_word_count),
            'avg_reading_level': float(avg_reading_level),
            'intent_coverage_score': intent_coverage,
            'navigation_efficiency': self.calculate_navigation_efficiency(site_map),
            'content_optimization_score': min(100, (avg_seo_score + avg_accessibility_score) / 2),
            'user_experience_score': self.calculate_ux_score(site_map)
        }
    
    def calculate_navigation_efficiency(self, site_map: Dict[str, PageData]) -> float:
        """Calculate navigation efficiency score"""
        if not site_map:
            return 0.0
        
        total_internal_links = sum(len(page.internal_links) for page in site_map.values())
        total_pages = len(site_map)
        
        # Average internal links per page (good sites have 3-5 internal links per page)
        avg_internal_links = total_internal_links / total_pages if total_pages else 0
        
        # Score based on ideal range
        if 3 <= avg_internal_links <= 5:
            return 100.0
        elif 2 <= avg_internal_links <= 6:
            return 80.0
        elif 1 <= avg_internal_links <= 7:
            return 60.0
        else:
            return 40.0
    
    def calculate_ux_score(self, site_map: Dict[str, PageData]) -> float:
        """Calculate user experience score"""
        if not site_map:
            return 0.0
        
        scores = []
        
        for page in site_map.values():
            page_score = 0
            
            # Content quality (40 points)
            if page.word_count >= 300:
                page_score += 20
            elif page.word_count >= 100:
                page_score += 10
            
            if 30 <= page.reading_level <= 60:  # Good readability
                page_score += 20
            elif 20 <= page.reading_level <= 70:
                page_score += 10
            
            # Navigation (30 points)
            if page.navigation_elements:
                page_score += 15
            
            if len(page.internal_links) >= 3:
                page_score += 15
            elif len(page.internal_links) >= 1:
                page_score += 10
            
            # Conversion optimization (30 points)
            if page.conversion_elements:
                page_score += 15
            
            if page.forms:
                page_score += 10
            
            # Contact information availability
            if page.contact_info['emails'] or page.contact_info['phones']:
                page_score += 5
            
            scores.append(page_score)
        
        return np.mean(scores) if scores else 0.0
    
    async def store_site_structure(self, site_structure: SiteStructure):
        """Store site structure in database"""
        if not self.db_service:
            return
        
        try:
            # Convert to dict for storage
            structure_data = asdict(site_structure)
            
            # Convert PageData objects to dicts
            site_map_dict = {}
            for url, page_data in site_structure.site_map.items():
                site_map_dict[url] = asdict(page_data)
                # Convert datetime to ISO string
                site_map_dict[url]['last_crawled'] = page_data.last_crawled.isoformat()
            
            structure_data['site_map'] = site_map_dict
            structure_data['last_full_crawl'] = site_structure.last_full_crawl.isoformat()
            
            # Store in database
            await self.db_service.store_site_structure(structure_data)
            
        except Exception as e:
            logger.error(f"Error storing site structure: {e}")
    
    async def analyze_user_intent(self, query: str, current_page: str, site_structure: SiteStructure) -> UserIntent:
        """Analyze user intent and provide intelligent recommendations"""
        
        query_lower = query.lower()
        intent_scores = {}
        
        # Calculate intent scores
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Determine primary intent
        if not intent_scores:
            primary_intent = 'information'
            confidence = 0.5
        else:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(1.0, intent_scores[primary_intent] / 5.0)
        
        # Get suggested pages based on intent
        suggested_pages = []
        if primary_intent in site_structure.intent_mapping:
            suggested_pages = site_structure.intent_mapping[primary_intent][:3]
        
        # Calculate conversion probability
        conversion_probability = self.calculate_conversion_probability(
            primary_intent, current_page, site_structure
        )
        
        # Generate recommended actions
        recommended_actions = self.generate_recommended_actions(
            primary_intent, query, site_structure
        )
        
        # Determine journey stage
        journey_stage = self.determine_intent_journey_stage(primary_intent, query)
        
        return UserIntent(
            intent_type=primary_intent,
            confidence=confidence,
            suggested_pages=suggested_pages,
            conversion_probability=conversion_probability,
            recommended_actions=recommended_actions,
            journey_stage=journey_stage
        )
    
    def calculate_conversion_probability(self, intent: str, current_page: str, site_structure: SiteStructure) -> float:
        """Calculate probability of conversion based on intent and context"""
        
        base_probabilities = {
            'product_inquiry': 0.7,
            'conversion': 0.9,
            'contact': 0.8,
            'support': 0.3,
            'navigation': 0.4,
            'information': 0.2
        }
        
        base_prob = base_probabilities.get(intent, 0.3)
        
        # Adjust based on current page
        if current_page in site_structure.site_map:
            page_data = site_structure.site_map[current_page]
            
            # Higher probability if already on decision-stage page
            if page_data.user_journey_stage == 'decision':
                base_prob *= 1.5
            elif page_data.user_journey_stage == 'consideration':
                base_prob *= 1.2
            
            # Higher probability if page has conversion elements
            if page_data.conversion_elements:
                base_prob *= 1.3
        
        return min(1.0, base_prob)
    
    def generate_recommended_actions(self, intent: str, query: str, site_structure: SiteStructure) -> List[str]:
        """Generate recommended actions based on intent"""
        
        actions = []
        
        if intent == 'product_inquiry':
            actions = [
                "Show product details and specifications",
                "Offer product comparison",
                "Provide pricing information",
                "Schedule a demo or consultation"
            ]
        elif intent == 'support':
            actions = [
                "Direct to FAQ or help documentation",
                "Offer to connect with support team",
                "Provide troubleshooting steps",
                "Search knowledge base"
            ]
        elif intent == 'navigation':
            actions = [
                "Help find the requested page or section",
                "Provide site map or navigation guide",
                "Offer search functionality",
                "Suggest related pages"
            ]
        elif intent == 'contact':
            actions = [
                "Provide contact information",
                "Show office locations and hours",
                "Offer to schedule a call",
                "Direct to contact form"
            ]
        elif intent == 'conversion':
            actions = [
                "Guide through sign-up process",
                "Highlight free trial or demo",
                "Explain benefits and value proposition",
                "Address common objections"
            ]
        else:
            actions = [
                "Provide relevant information",
                "Suggest related pages",
                "Offer additional assistance",
                "Ask clarifying questions"
            ]
        
        return actions
    
    def determine_intent_journey_stage(self, intent: str, query: str) -> str:
        """Determine user journey stage based on intent and query"""
        
        query_lower = query.lower()
        
        # Decision stage indicators
        decision_keywords = ['buy', 'purchase', 'price', 'cost', 'demo', 'trial', 'contact', 'quote']
        if intent in ['conversion', 'contact'] or any(kw in query_lower for kw in decision_keywords):
            return 'decision'
        
        # Consideration stage indicators
        consideration_keywords = ['compare', 'features', 'benefits', 'vs', 'difference', 'options']
        if intent == 'product_inquiry' or any(kw in query_lower for kw in consideration_keywords):
            return 'consideration'
        
        # Default to awareness
        return 'awareness'
    
    async def get_navigation_suggestions(self, query: str, current_page: str, site_structure: SiteStructure) -> List[Dict[str, Any]]:
        """Get intelligent navigation suggestions based on query and site structure"""
        
        suggestions = []
        query_lower = query.lower()
        
        # Search through site map for relevant pages
        for url, page_data in site_structure.site_map.items():
            relevance_score = 0
            
            # Check title relevance
            title_words = page_data.title.lower().split()
            query_words = query_lower.split()
            title_matches = sum(1 for word in query_words if word in title_words)
            relevance_score += title_matches * 3
            
            # Check content relevance
            content_matches = sum(1 for word in query_words if word in page_data.content.lower())
            relevance_score += content_matches
            
            # Check keyword relevance
            keyword_matches = sum(1 for word in query_words if word in [kw.lower() for kw in page_data.keywords])
            relevance_score += keyword_matches * 2
            
            if relevance_score > 0:
                suggestions.append({
                    'url': url,
                    'title': page_data.title,
                    'description': page_data.description,
                    'relevance_score': relevance_score,
                    'page_type': page_data.page_type,
                    'journey_stage': page_data.user_journey_stage
                })
        
        # Sort by relevance score
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
