"""
Text processing and cleaning utilities.
Refactored to use semantic HTML parsing instead of fragile regex patching.
"""
from bs4 import BeautifulSoup, NavigableString, Tag
import re
import html


def normalize_metadata_text(value: str) -> str:
    """Normalize short metadata strings (titles/subjects) for podcast apps.

    This is intentionally conservative: it focuses on fixing common
    copy/paste/HTML boundary issues (missing spaces) without re-writing
    the content.
    """
    if not value:
        return ""

    text = html.unescape(value)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()

    # Fix missing space after possessives like "Nvidia’sweakness" -> "Nvidia’s weakness".
    # Preserve the apostrophe style (straight vs curly).
    text = re.sub(r"([A-Za-z])([’'])s(?=[A-Za-z])", r"\1\2s ", text)

    # Improve readability when emojis are adjacent to words.
    # Covers most modern emoji blocks; safe no-op on ASCII-only titles.
    emoji_range = r"\U0001F300-\U0001FAFF"
    text = re.sub(fr"(\w)([{emoji_range}])", r"\1 \2", text)
    text = re.sub(fr"([{emoji_range}])(\w)", r"\1 \2", text)

    # Basic punctuation spacing (avoid touching URLs by keeping it minimal).
    text = re.sub(r",(?=\S)", ", ", text)

    return re.sub(r"\s+", " ", text).strip()

class TLDRTextProcessor:
    """
    Parses TLDR email HTML into structured blocks for TTS generation.
    """
    
    SECTION_HEADERS = [
        "Headlines & Launches", "Deep Dives & Analysis", 
        "Engineering & Research", "Miscellaneous", "Quick Links",
        "Headlines and Launches", "Deep Dives and Analysis",
        "Engineering and Research"
    ]

    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.clean_text = ""

    def process(self):
        """Main execution pipeline."""
        self._clean_soup()
        blocks = self._extract_blocks()
        self.clean_text = self._compile_text(blocks)
        return self.clean_text

    def _clean_soup(self):
        """Remove unwanted HTML elements before extraction."""
        # Remove invisible/utility tags
        for tag in self.soup(['script', 'style', 'head', 'meta', 'iframe', 'button', 'input']):
            tag.decompose()
            
        # PREHEADER / NAVIGATION REMOVAL
        # The email usually starts with a "preheader" div (invisible) and then "Sign Up | View Online"
        # We find the "View Online" link and remove it AND preceding siblings if they are small text.
        
        # 1. Find the Main Navigation Bar ("Sign Up | Advertise | View Online")
        nav_text_markers = ['View Online', 'Sign Up', 'Advertise']
        for marker in nav_text_markers:
            for tag in self.soup.find_all(string=re.compile(re.escape(marker), re.I)):
                # This is likely the top nav.
                # Remove the containing table or div.
                container = tag.find_parent(['table', 'div'])
                if container:
                    # Heuristic: If this container is huge (contains the whole email), don't delete it.
                    # Only delete if it's relatively small (e.g. < 500 chars).
                    if len(container.get_text()) < 500:
                        container.decompose()

        # 2. Remove Preheader (often hidden div)
        # Often has style="display:none" or class="preheader"
        for tag in self.soup.find_all('div'):
            style = tag.get('style', '').lower()
            if 'display:none' in style or 'display: none' in style or 'opacity:0' in style:
                tag.decompose()
                
        # 3. Remove Branding Headers (TLDR AI logo/text)
        # Look for the main title "TLDR AI" or date in header
        for tag in self.soup.find_all(string=re.compile(r'^\s*TLDR\s+AI\s*$', re.I)):
            if len(tag.strip()) < 20:
                tag.find_parent(['tr', 'td', 'div']).decompose()

        # Remove Date Line (YYYY-MM-DD)
        for tag in self.soup.find_all(string=re.compile(r'\d{4}-\d{2}-\d{2}')):
            if len(tag.strip()) < 20:
                parent = tag.find_parent(['tr', 'td', 'div'])
                if parent: parent.decompose()

        # Remove Footer Content
        # Look for "Manage your subscriptions" or "Unsubscribe"
        footer_keywords = ['Manage your subscriptions', 'Unsubscribe', 'Want to advertise?']
        for keyword in footer_keywords:
            for tag in self.soup.find_all(string=re.compile(re.escape(keyword), re.I)):
                # Traverse up to find the container block (usually a div or table row)
                # and remove it, but be careful not to remove the whole body.
                parent = tag.find_parent(['div', 'tr'])
                if parent:
                    parent.decompose()

    def _extract_blocks(self):
        """
        Walk the DOM to extract meaningful text blocks.
        Returns a list of dicts: {'type': 'header|story|sponsor', 'content': '...'}
        """
        blocks = []
        
        # Generator to yield strings and images in document order
        def generate_content_nodes(root):
            for element in root.descendants:
                if isinstance(element, NavigableString):
                    if element.strip():
                        yield ('text', element)
                elif element.name == 'img':
                    yield ('img', element)

        content_nodes = list(generate_content_nodes(self.soup))
        
        current_section = "Intro"

        for i, (kind, node) in enumerate(content_nodes):
            if kind == 'img':
                # Skip normal images, we will peek at them from text nodes if needed
                continue
                
            # It's text
            s = node
            text = s.replace('\xa0', ' ').strip()
            text = re.sub(r'\s+', ' ', text).strip()
            if not text:
                continue
            
            # Skip very short navigation artifacts or common garbage
            if len(text) < 3 and not re.match(r'[A-Za-z0-9]', text):
                continue
            
            # Explicit Ignore List
            if re.match(r'^\s*TLDR\s*$', text, re.I) or re.match(r'\d{4}-\d{2}-\d{2}', text):
                continue

            # Remove spaced TLDR
            if re.match(r'^\s*T\s*L\s*D\s*R\s*', text, re.I):
                continue
            
            # Remove isolated "html" strings if they appear
            if text.lower() == 'html':
                continue
                
            # IDENTIFY CONTEXT
            parent = s.parent
            is_bold = False
            # Check for bold styling
            if parent.name in ['strong', 'b', 'h1', 'h2', 'h3', 'h4']:
                is_bold = True
            elif parent.parent and parent.parent.name in ['strong', 'b', 'h1', 'h2', 'h3', 'h4']:
                 is_bold = True # Check grandparent
            elif 'font-weight' in str(parent.get('style', '')).lower() and 'bold' in str(parent.get('style', '')):
                is_bold = True

            # 1. SPONSOR CHECK
            # Check for "Together With" phrasing
            together_complex = re.search(r'\bTogether\s+With\s*(.*)', text, re.I)
            
            if together_complex:
                remainder = together_complex.group(1).strip()
                
                # Case A: "Together With Framer" (All in one text node)
                if len(remainder) > 2:
                     blocks.append({'type': 'marker', 'content': f'Together with {remainder}'})
                     continue
                
                # Case B: "Together With" (followed by something else, possibly an image)
                else:
                    sponsor_found = False
                    # Look ahead at the next few nodes (limit 3)
                    for offset in range(1, 4):
                        if i + offset >= len(content_nodes): break
                        
                        next_kind, next_node = content_nodes[i + offset]
                        
                        if next_kind == 'img':
                            # Found an image! Check alt text or title.
                            alt_text = next_node.get('alt') or next_node.get('title', '')
                            if alt_text and len(alt_text) > 2:
                                blocks.append({'type': 'marker', 'content': f'Together with {alt_text}'})
                                sponsor_found = True
                                break
                        elif next_kind == 'text':
                             # If we hit text immediately that looks like a name (short, maybe bold?), take it.
                             next_text_val = next_node.strip()
                             # If it's short and capitalised, likely the sponsor name
                             if len(next_text_val) < 30 and (next_text_val[0].isupper() or len(next_text_val.split()) < 3):
                                  blocks.append({'type': 'marker', 'content': f'Together with {next_text_val}'})
                                  # We 'consumed' this text effectively, but the loop will process it again.
                                  # That's okay, "Framer" as a headline is harmless, or we can skip it?
                                  # Let's just output it. "Together With Framer... Framer" is redundancy but acceptable.
                                  # Ideally we mark it as consumed, but let's stick to simple first.
                                  sponsor_found = True
                                  break
                    
                    if not sponsor_found:
                        # Fallback
                        blocks.append({'type': 'marker', 'content': 'Together with '})
                    continue

            if re.search(r'Sponsored\s+By', text, re.I):
                blocks.append({'type': 'marker', 'content': 'Sponsored by:'})
                continue
            
            # 2. SECTION HEADER CHECK
            # Check against known category list
            is_section_header = False
            for h in self.SECTION_HEADERS:
                if h.lower() in text.lower() and len(text) < 50:
                    blocks.append({'type': 'section_header', 'content': text.title().replace('&', 'and') + "."})
                    current_section = text
                    is_section_header = True
                    break
            if is_section_header:
                continue

            # 3. STORY HEADLINE CHECK
            # Heuristic: Bold, Upper Case, or distinct styling, followed by longer text.
            # TLDR headlines are usually links <a> inside <strong> or <span> having bold style.
            if is_bold and (text.isupper() or len(text.split()) < 20):
                # Clean up known casing issues (e.g. FRAMER -> Framer)
                if text.isupper() and len(text) > 4:
                    text = text.title()
                
                blocks.append({'type': 'headline', 'content': text})
                continue
                
            # 4. BODY TEXT
            # Normal paragraph text.
            blocks.append({'type': 'body', 'content': text})

        return blocks

    def _compile_text(self, blocks):
        """
        Convert structured blocks into final TTS script strings.
        """
        output_parts = []
        
        for i, block in enumerate(blocks):
            content = block['content']
            
            # TEXT CLEANING (Regex still useful here for fine-tuning)
            # Remove URLs
            content = re.sub(r'http\S+', '', content)
            # Remove [1], [2] refs
            content = re.sub(r'\[\d+\]', '', content)
            # Remove read times e.g. (5 minute read)
            content = re.sub(r'\s*\(\d+\s+minutes?\s+read\)', '', content, flags=re.IGNORECASE)
            # Remove (Sponsor) text
            content = re.sub(r'\s*\(Sponsor(?:ed)?\)', '', content, flags=re.IGNORECASE)
            # Fix spacing
            content = content.strip()
            
            if not content:
                continue

            if block['type'] == 'marker':
                output_parts.append("\n\n" + content + " ") 
                
            elif block['type'] == 'section_header':
                output_parts.append("\n\n\n" + content + "\n\n")
                
            elif block['type'] == 'headline':
                # Headlines need a pause after them.
                if content.isupper():
                    content = content.title()
                
                # Ensure it ends with punctuation if it's a headline? 
                if not content[-1] in '.!?,:':
                    content += "."
                
                output_parts.append("\n\n" + content + "\n")
                
            elif block['type'] == 'body':
                # Body text. Ensure it ends with punctuation if it looks like a sentence.
                # Collapse "Link" texts that might be floating (e.g. "Read more")
                if re.match(r'^(Read more|Source|Link)$', content, re.I):
                    continue
                
                # Manual fixes for clean reading
                content = content.replace("..", ".")
                    
                output_parts.append(content + " ")

        # Join and finalize
        full_text = "".join(output_parts)

        # Remove footer content (hard cutoff at common footer markers)
        footer_markers = [
            "Love TLDR",
            "Track your referrals",
            "Want to advertise",
            "Want to work at",
            "Manage your subscriptions",
            "Unsubscribe",
            "Update your profile",
        ]
        for marker in footer_markers:
            if marker.lower() in full_text.lower():
                full_text = full_text.split(marker, 1)[0].rstrip()
                break

        # Merge TLDR + Together-with into a single line (no pause)
        full_text = re.sub(
            r'^\s*(?:T\s*L\s*D\s*R|TLDR)\s*\n+\s*Together\s+with\s+',
            'TLDR Together with ',
            full_text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        
        # FINAL CLEANUP
        # Collapse multiple spaces
        full_text = re.sub(r' +', ' ', full_text)
        # Collapse excessive newlines (more than 2)
        full_text = re.sub(r'\n{4,}', '\n\n\n', full_text)
        
        return full_text.strip()

# ==========================================
# COMPATIBILITY FUNCTIONS (Wrapper Interface)
# ==========================================

def clean_html_content(html_content):
    """Legacy wrapper: Returns HTML as-is so the new processor can parse it."""
    # We strip whitespace but keep HTML structure intact.
    return html_content.strip()

def clean_text_for_tts(text_or_html, verbose=False):
    """
    Main entry point. Now accepts HTML or Text.
    """
    # Simply instance the processor and run
    # If the input is somehow already plain text (no tags), BeautifulSoup handles it gracefully 
    # (it just creates a soup with one string), so this is safe.
    processor = TLDRTextProcessor(text_or_html)
    text = processor.process()
    
    if verbose:
        print(f"[TLDRTextProcessor] Final TTS text length: {len(text)}")
        
    return text

def extract_show_notes(html_content):
    """
    Extract headlines and links from HTML content for podcast show notes.
    """
    links = extract_show_note_links(html_content)

    lines = []
    for link in links:
        lines.append(f"* [{link['text']}]({link['url']})")

    return "\n".join(lines)


def extract_show_note_links(html_content):
    """Extract a de-duped list of headline-like links from the digest HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    def clean(t):
        return re.sub(r'\s+', ' ', t).strip()

    for a in soup.find_all('a', href=True):
        text = clean(a.get_text())
        href = a['href']
        
        if not text or len(text) < 5:
            continue

        # Only keep web links that a podcast client can open.
        if not (href.startswith('http://') or href.startswith('https://')):
            continue
            
        skip_phrases = [
            'sign up', 'advertise', 'view online', 'unsubscribe', 
            'manage your subscriptions', 'update your profile',
            'privacy policy', 'terms of service', 'sponsor', 'read more',
            'tldr ai', 'referral', 'login'
        ]
        
        if any(phrase in text.lower() for phrase in skip_phrases):
            continue
            
        is_bold = False
        parsed_parents = list(a.parents)
        for parent in parsed_parents[:3]: 
            if parent.name in ['strong', 'b', 'h1', 'h2', 'h3']:
                is_bold = True
                break
            if parent.get('style') and 'font-weight' in parent['style']:
                 is_bold = True
                 break
        
        if is_bold or len(text) > 15:
            if not any(l['url'] == href for l in links):
                links.append({'text': text, 'url': href})

    return links
