"""
Data Curation Pipeline for Python API Documentation

Collects and formats Python library documentation into instruction-following
training examples for fine-tuning.
"""
import requests
from bs4 import BeautifulSoup
import html2text
import json
import re
from typing import List, Dict
from pathlib import Path
from tqdm import tqdm
import time


class DocumentationScraper:
    """Scrapes Python library documentation"""
    
    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        
    def scrape_library(self, library_name: str, base_url: str) -> List[Dict]:
        """
        Scrape documentation for a Python library
        
        Args:
            library_name: Name of the library (e.g., 'requests')
            base_url: Base URL of documentation
            
        Returns:
            List of documentation sections
        """
        print(f"Scraping {library_name} documentation...")
        sections = []
        
        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find main content area (adjust selectors based on docs structure)
            content_divs = soup.find_all(['div', 'section'], class_=re.compile('content|documentation|main'))
            
            for div in content_divs:
                # Extract headings and content
                headings = div.find_all(['h1', 'h2', 'h3'])
                
                for heading in headings:
                    section_title = heading.get_text().strip()
                    
                    # Get content until next heading
                    content_parts = []
                    for sibling in heading.find_next_siblings():
                        if sibling.name in ['h1', 'h2', 'h3']:
                            break
                        content_parts.append(str(sibling))
                    
                    if content_parts:
                        content_html = '\n'.join(content_parts)
                        content_text = self.html_converter.handle(content_html)
                        
                        sections.append({
                            'library': library_name,
                            'title': section_title,
                            'content': content_text,
                            'url': base_url
                        })
            
            print(f"✓ Scraped {len(sections)} sections from {library_name}")
            
        except Exception as e:
            print(f"✗ Error scraping {library_name}: {e}")
        
        return sections


class DataFormatter:
    """Formats scraped documentation into instruction-response pairs"""
    
    def __init__(self):
        self.instruction_templates = [
            "How do I use {function} in {library}?",
            "Explain {function} from {library}",
            "What is {function} in {library}?",
            "Show me an example of {function} from {library}",
            "How does {function} work in {library}?",
        ]
    
    def extract_code_examples(self, content: str) -> List[str]:
        """Extract code blocks from content"""
        code_blocks = re.findall(r'```python\n(.*?)```', content, re.DOTALL)
        return code_blocks
    
    def extract_functions(self, content: str) -> List[str]:
        """Extract function/method names from content"""
        # Look for function patterns
        functions = re.findall(r'`([a-zA-Z_][a-zA-Z0-9_.]*\(.*?\))`', content)
        functions += re.findall(r'def ([a-zA-Z_][a-zA-Z0-9_]*)', content)
        return list(set(functions))
    
    def create_training_examples(self, sections: List[Dict]) -> List[Dict]:
        """
        Convert documentation sections into training examples
        
        Args:
            sections: List of documentation sections
            
        Returns:
            List of instruction-response pairs
        """
        examples = []
        
        print("Creating training examples...")
        
        for section in tqdm(sections):
            library = section['library']
            title = section['title']
            content = section['content']
            
            # Skip very short or very long sections
            if len(content) < 100 or len(content) > 5000:
                continue
            
            # Extract functions mentioned in this section
            functions = self.extract_functions(content)
            
            if functions:
                # Create examples for each function
                for func in functions[:3]:  # Limit to 3 functions per section
                    # Pick a random instruction template
                    import random
                    template = random.choice(self.instruction_templates)
                    instruction = template.format(function=func, library=library)
                    
                    # Use section content as response
                    response = self._clean_content(content)
                    
                    examples.append({
                        'instruction': instruction,
                        'response': response,
                        'library': library,
                        'function': func
                    })
            else:
                # Create general example from title
                instruction = f"Explain {title} in {library}"
                response = self._clean_content(content)
                
                examples.append({
                    'instruction': instruction,
                    'response': response,
                    'library': library,
                    'function': None
                })
        
        print(f"✓ Created {len(examples)} training examples")
        return examples
    
    def _clean_content(self, content: str) -> str:
        """Clean and format content"""
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()
        
        # Limit length
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        return content


class DatasetCreator:
    """Creates train/validation/test splits"""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def create_splits(self, examples: List[Dict], train_ratio: float = 0.8, 
                     val_ratio: float = 0.1):
        """
        Create train/validation/test splits
        
        Args:
            examples: List of training examples
            train_ratio: Proportion for training (default: 0.8)
            val_ratio: Proportion for validation (default: 0.1)
        """
        import random
        
        # Shuffle examples
        random.shuffle(examples)
        
        # Calculate split indices
        n = len(examples)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        # Split data
        train_data = examples[:train_end]
        val_data = examples[train_end:val_end]
        test_data = examples[val_end:]
        
        # Save splits
        self._save_jsonl(train_data, self.output_dir / "training_data.jsonl")
        self._save_jsonl(val_data, self.output_dir / "validation_data.jsonl")
        self._save_jsonl(test_data, self.output_dir / "test_data.jsonl")
        
        print(f"\n✓ Dataset created:")
        print(f"  - Training:   {len(train_data)} examples")
        print(f"  - Validation: {len(val_data)} examples")
        print(f"  - Test:       {len(test_data)} examples")
        print(f"  - Saved to:   {self.output_dir}/")
    
    def _save_jsonl(self, data: List[Dict], filepath: Path):
        """Save data in JSONL format"""
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')


class PythonAPICurator:
    """Main pipeline for curating Python API documentation"""
    
    # Popular Python libraries with documentation URLs
    LIBRARY_URLS = {
        'requests': 'https://requests.readthedocs.io/en/latest/user/quickstart/',
        'pandas': 'https://pandas.pydata.org/docs/user_guide/10min.html',
        'numpy': 'https://numpy.org/doc/stable/user/quickstart.html',
    }
    
    def __init__(self, output_dir: str = "data"):
        self.scraper = DocumentationScraper()
        self.formatter = DataFormatter()
        self.dataset_creator = DatasetCreator(output_dir)
    
    def curate(self, libraries: List[str] = None):
        """
        Run complete curation pipeline
        
        Args:
            libraries: List of library names to curate (default: all)
        """
        if libraries is None:
            libraries = list(self.LIBRARY_URLS.keys())
        
        print("="*70)
        print("Python API Documentation Curation Pipeline")
        print("="*70)
        
        # Scrape documentation
        all_sections = []
        for library in libraries:
            if library in self.LIBRARY_URLS:
                url = self.LIBRARY_URLS[library]
                sections = self.scraper.scrape_library(library, url)
                all_sections.extend(sections)
                time.sleep(1)  # Be polite to servers
        
        if not all_sections:
            print("✗ No documentation scraped. Check URLs or connectivity.")
            return
        
        # Format into training examples
        examples = self.formatter.create_training_examples(all_sections)
        
        if not examples:
            print("✗ No training examples created.")
            return
        
        # Create dataset splits
        self.dataset_creator.create_splits(examples)
        
        print("\n" + "="*70)
        print("✓ Data curation complete!")
        print("="*70)


if __name__ == "__main__":
    # Example usage
    curator = PythonAPICurator(output_dir="data")
    curator.curate(libraries=['requests', 'pandas', 'numpy'])
