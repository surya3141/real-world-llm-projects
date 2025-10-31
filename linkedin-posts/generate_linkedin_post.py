#!/usr/bin/env python3
"""
LinkedIn Post Generator for Medium Articles

This script helps generate LinkedIn posts from Medium articles by extracting
key information and providing a structured template for post creation.

Usage:
    python generate_linkedin_post.py <article_path> [options]
    
Example:
    python generate_linkedin_post.py ../articles/article-01-introduction.md --output post-01-draft.md
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List, Tuple
import sys


class LinkedInPostGenerator:
    """Generate LinkedIn posts from Medium articles."""
    
    def __init__(self, article_path: str):
        self.article_path = Path(article_path)
        self.article_content = self._read_article()
        self.metadata = self._extract_metadata()
        
    def _read_article(self) -> str:
        """Read the article content."""
        if not self.article_path.exists():
            raise FileNotFoundError(f"Article not found: {self.article_path}")
        
        with open(self.article_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_metadata(self) -> Dict:
        """Extract metadata from the article."""
        metadata = {
            'title': self._extract_title(),
            'key_points': self._extract_key_points(),
            'problems': self._extract_problems(),
            'solutions': self._extract_solutions(),
            'metrics': self._extract_metrics(),
            'word_count': len(self.article_content.split()),
            'estimated_read_time': self._calculate_read_time()
        }
        return metadata
    
    def _extract_title(self) -> str:
        """Extract the main title from the article."""
        # Look for markdown H1 headers
        match = re.search(r'^#\s+(.+)$', self.article_content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return "Untitled Article"
    
    def _extract_key_points(self) -> List[str]:
        """Extract key points from the article."""
        key_points = []
        
        # Look for sections with ### headers
        sections = re.findall(r'^###\s+(.+)$', self.article_content, re.MULTILINE)
        key_points.extend(sections[:6])  # Take first 6 sections
        
        # Look for bold statements that might be key points
        bold_statements = re.findall(r'\*\*(.+?)\*\*', self.article_content)
        key_points.extend([s for s in bold_statements if 10 < len(s) < 100][:3])
        
        return list(set(key_points))[:6]  # Return unique, max 6 points
    
    def _extract_problems(self) -> List[str]:
        """Extract problem statements from the article."""
        problems = []
        
        # Look for common problem indicators
        problem_patterns = [
            r'problem[s]?[:\s]+(.+?)(?:\n|$)',
            r'challenge[s]?[:\s]+(.+?)(?:\n|$)',
            r'issue[s]?[:\s]+(.+?)(?:\n|$)',
            r'limitation[s]?[:\s]+(.+?)(?:\n|$)',
        ]
        
        for pattern in problem_patterns:
            matches = re.findall(pattern, self.article_content, re.IGNORECASE)
            problems.extend([m.strip() for m in matches if len(m.strip()) > 20])
        
        return problems[:4]  # Return first 4 problems
    
    def _extract_solutions(self) -> List[str]:
        """Extract solution statements from the article."""
        solutions = []
        
        # Look for common solution indicators
        solution_patterns = [
            r'solution[s]?[:\s]+(.+?)(?:\n|$)',
            r'approach[es]?[:\s]+(.+?)(?:\n|$)',
            r'implementation[s]?[:\s]+(.+?)(?:\n|$)',
            r'my\s+solution[:\s]+(.+?)(?:\n|$)',
        ]
        
        for pattern in solution_patterns:
            matches = re.findall(pattern, self.article_content, re.IGNORECASE)
            solutions.extend([m.strip() for m in matches if len(m.strip()) > 20])
        
        return solutions[:4]  # Return first 4 solutions
    
    def _extract_metrics(self) -> List[str]:
        """Extract metrics and statistics from the article."""
        metrics = []
        
        # Look for percentages
        percentages = re.findall(r'(\d+%\s+[^.!?\n]+)', self.article_content)
        metrics.extend(percentages[:3])
        
        # Look for cost/time savings
        savings = re.findall(r'(\$\d+[KkMm]?\s+[^.!?\n]+)', self.article_content)
        metrics.extend(savings[:2])
        
        # Look for improvement metrics
        improvements = re.findall(r'(\d+x\s+[^.!?\n]+)', self.article_content)
        metrics.extend(improvements[:2])
        
        return metrics[:5]  # Return first 5 metrics
    
    def _calculate_read_time(self) -> int:
        """Calculate estimated read time in minutes."""
        words = len(self.article_content.split())
        return max(1, round(words / 200))  # Average reading speed: 200 words/min
    
    def generate_post(self, style: str = 'default') -> str:
        """Generate a LinkedIn post based on the extracted metadata."""
        
        if style == 'technical':
            return self._generate_technical_post()
        elif style == 'story':
            return self._generate_story_post()
        elif style == 'question':
            return self._generate_question_post()
        else:
            return self._generate_default_post()
    
    def _generate_default_post(self) -> str:
        """Generate a default style LinkedIn post."""
        post = f"""# LinkedIn Post: {self.metadata['title']}

---

🚀 **[ATTENTION-GRABBING HOOK]**

[Replace with your hook - Use the template guide for ideas]

**The Problem:**

"""
        # Add extracted problems
        if self.metadata['problems']:
            for problem in self.metadata['problems'][:3]:
                post += f"❌ {problem}\n"
        else:
            post += "❌ [Problem point 1]\n"
            post += "❌ [Problem point 2]\n"
            post += "❌ [Problem point 3]\n"
        
        post += "\n**But there's a solution—and I've documented it.**\n\n"
        post += "I just published a comprehensive article on Medium exploring:\n\n"
        
        # Add key points
        emojis = ['🔍', '💡', '⚡', '🎯', '📈', '🚀']
        for i, point in enumerate(self.metadata['key_points'][:6]):
            emoji = emojis[i] if i < len(emojis) else '🔹'
            post += f"{emoji} **{point}**\n\n"
        
        # Add metrics if available
        if self.metadata['metrics']:
            post += "**Key Results:**\n\n"
            for metric in self.metadata['metrics'][:3]:
                post += f"✅ {metric}\n"
            post += "\n"
        
        post += """**My Key Insight:**

[Share one memorable takeaway from the article]

👉 **Read the full article on Medium:** [INSERT YOUR MEDIUM LINK]

---

💭 **Question for the community:**

[Ask an engaging question related to the article topic]

What's your experience with this? Share your thoughts below! 👇

---

#AI #MachineLearning #DataScience #TechArticle #Medium #[AddRelevantTags]

---

**📊 Article Stats:**
"""
        post += f"- Read Time: {self.metadata['estimated_read_time']} minutes\n"
        post += "- Level: [Beginner/Intermediate/Advanced]\n"
        post += f"- Focus: {self.metadata['title']}\n\n"
        
        post += "**P.S.** If you find this valuable, please share with your network!\n"
        
        return post
    
    def _generate_technical_post(self) -> str:
        """Generate a technical deep-dive style post."""
        post = f"""# LinkedIn Post: {self.metadata['title']} (Technical Deep-Dive)

---

🔧 **Technical Deep-Dive: {self.metadata['title']}**

After {self.metadata['estimated_read_time']} months of research and implementation, I've documented my journey building [system/solution].

**The Technical Challenge:**

"""
        # Add problems
        for problem in (self.metadata['problems'] or ["Challenge 1", "Challenge 2"])[:2]:
            post += f"⚠️ {problem}\n"
        
        post += "\n**My Implementation:**\n\n"
        
        # Add key technical points
        for point in self.metadata['key_points'][:5]:
            post += f"🔹 {point}\n"
        
        post += "\n**Technical Metrics:**\n\n"
        
        # Add metrics
        for metric in (self.metadata['metrics'] or ["Metric 1", "Metric 2"])[:4]:
            post += f"📊 {metric}\n"
        
        post += """\n👉 **Full technical breakdown on Medium:** [INSERT LINK]

The article includes:
✅ Architecture diagrams
✅ Code snippets and implementation details
✅ Benchmark comparisons
✅ Lessons learned and gotchas

---

💭 **For the engineers:**

What's your approach to [relevant technical challenge]? Any alternative solutions you'd recommend?

---

#TechnicalArticle #SoftwareEngineering #SystemDesign #AI #MachineLearning #MLOps
"""
        return post
    
    def _generate_story_post(self) -> str:
        """Generate a personal story style post."""
        post = f"""# LinkedIn Post: {self.metadata['title']} (Personal Story)

---

**[X] years ago, I [past situation].**

**Today, I [current situation].**

The journey wasn't straightforward. I wrote about this transformation on Medium, and the lessons might surprise you.

**What I learned:**

"""
        for point in self.metadata['key_points'][:4]:
            post += f"💡 {point}\n"
        
        post += """\n**The results speak for themselves:**

"""
        for metric in (self.metadata['metrics'] or ["Result 1", "Result 2"])[:3]:
            post += f"✅ {metric}\n"
        
        post += """\n**Why I'm sharing this:**

[Personal motivation - why this matters to you]

👉 **Read my full story on Medium:** [INSERT LINK]

---

💭 **Your turn:**

What's been your biggest learning moment in your career? I'd love to hear your story.

---

#CareerGrowth #PersonalDevelopment #TechJourney #LearningInPublic
"""
        return post
    
    def _generate_question_post(self) -> str:
        """Generate a provocative question style post."""
        post = f"""# LinkedIn Post: {self.metadata['title']} (Question Hook)

---

🤔 **Hot take: [Provocative statement related to your article]**

Most professionals don't realize [surprising insight]. I spent weeks researching this and wrote a detailed analysis.

**Here's what the data shows:**

"""
        for metric in (self.metadata['metrics'] or ["Finding 1", "Finding 2"])[:3]:
            post += f"📊 {metric}\n"
        
        post += """\n**In my article, I explore:**

"""
        for i, point in enumerate(self.metadata['key_points'][:5], 1):
            post += f"{i}️⃣ {point}\n"
        
        post += """\n**The implications are significant:**

[Explain the broader impact or urgency]

👉 **Full analysis on Medium:** [INSERT LINK]

---

💭 **Agree or disagree?**

Comment your thoughts—especially if you think I'm wrong! Let's have a healthy debate. 👇

---

#TechDebate #IndustryInsights #ThoughtLeadership #AI #FutureOfWork
"""
        return post
    
    def generate_multiple_variations(self) -> Dict[str, str]:
        """Generate multiple post variations."""
        return {
            'default': self.generate_post('default'),
            'technical': self.generate_post('technical'),
            'story': self.generate_post('story'),
            'question': self.generate_post('question')
        }
    
    def save_post(self, output_path: str, style: str = 'default'):
        """Save the generated post to a file."""
        post = self.generate_post(style)
        output_file = Path(output_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(post)
        
        print(f"✅ LinkedIn post generated: {output_file}")
        print(f"📊 Article stats: {self.metadata['estimated_read_time']} min read")
        print(f"🔑 Key points found: {len(self.metadata['key_points'])}")
        print(f"📈 Metrics extracted: {len(self.metadata['metrics'])}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate LinkedIn posts from Medium articles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_linkedin_post.py ../articles/article-01-introduction.md
  python generate_linkedin_post.py ../articles/article-02-rag.md --style technical
  python generate_linkedin_post.py ../articles/article-03-agents.md --output my-post.md --style story
  python generate_linkedin_post.py ../articles/article-04-finetuning.md --all-styles

Styles:
  default   - Balanced post suitable for most articles (default)
  technical - Deep technical dive for engineering audiences
  story     - Personal narrative with transformation arc
  question  - Provocative question to spark debate
        """
    )
    
    parser.add_argument(
        'article',
        help='Path to the Medium article (markdown file)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: auto-generated from article name)'
    )
    
    parser.add_argument(
        '--style', '-s',
        choices=['default', 'technical', 'story', 'question'],
        default='default',
        help='Post style/template to use (default: default)'
    )
    
    parser.add_argument(
        '--all-styles',
        action='store_true',
        help='Generate all style variations'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview the post without saving'
    )
    
    args = parser.parse_args()
    
    try:
        # Create generator
        generator = LinkedInPostGenerator(args.article)
        
        if args.all_styles:
            # Generate all variations
            variations = generator.generate_multiple_variations()
            article_name = Path(args.article).stem
            
            for style_name, content in variations.items():
                output_file = f"{article_name}-linkedin-{style_name}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Generated: {output_file}")
            
            print(f"\n🎉 All {len(variations)} style variations generated!")
        
        elif args.preview:
            # Just preview without saving
            post = generator.generate_post(args.style)
            print("\n" + "="*80)
            print("PREVIEW")
            print("="*80 + "\n")
            print(post)
            print("\n" + "="*80)
        
        else:
            # Generate single post
            if args.output:
                output_file = args.output
            else:
                article_name = Path(args.article).stem
                output_file = f"{article_name}-linkedin-post.md"
            
            generator.save_post(output_file, args.style)
            
            print("\n💡 Next steps:")
            print("   1. Review the generated post")
            print("   2. Replace placeholders with your content")
            print("   3. Add your Medium article link")
            print("   4. Customize the hook and key insight")
            print("   5. Add relevant hashtags for your audience")
            print("   6. Review with LINKEDIN-POST-TEMPLATE.md for best practices")
    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
