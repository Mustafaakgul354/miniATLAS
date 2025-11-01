"""Selector utilities for semantic and role-based element location."""

from typing import List, Optional

from playwright.async_api import Locator, Page


class SelectorBuilder:
    """Helper for building robust selectors."""
    
    @staticmethod
    def by_text(text: str, exact: bool = False) -> str:
        """Create text-based selector."""
        if exact:
            return f'text="{text}"'
        return f'text={text}'
    
    @staticmethod
    def by_role(role: str, name: Optional[str] = None) -> str:
        """Create ARIA role-based selector."""
        if name:
            return f'role={role}[name="{name}"]'
        return f'role={role}'
    
    @staticmethod
    def by_label(label: str) -> str:
        """Create label-based selector for form fields."""
        return f'label={label}'
    
    @staticmethod
    def by_placeholder(placeholder: str) -> str:
        """Create placeholder-based selector."""
        return f'[placeholder="{placeholder}"]'
    
    @staticmethod
    def by_test_id(test_id: str) -> str:
        """Create data-testid based selector."""
        return f'[data-testid="{test_id}"]'


async def find_element_near(
    page: Page,
    target_text: str,
    near_text: str,
    max_distance: int = 300
) -> Optional[Locator]:
    """Find element near another element (useful for forms)."""
    try:
        # Find the reference element
        reference = page.locator(f'text={near_text}').first
        
        # Use Playwright's position-based filtering
        target = page.locator(f'text={target_text}')
        
        # Get bounding boxes and filter by distance
        ref_box = await reference.bounding_box()
        if not ref_box:
            return None
        
        count = await target.count()
        for i in range(count):
            element = target.nth(i)
            box = await element.bounding_box()
            if box:
                # Calculate distance
                distance = ((box['x'] - ref_box['x']) ** 2 + 
                           (box['y'] - ref_box['y']) ** 2) ** 0.5
                if distance <= max_distance:
                    return element
        
        return None
    except Exception:
        return None


async def get_interactive_elements(page: Page) -> List[dict]:
    """Get all interactive elements on the page."""
    elements = []
    
    # Buttons
    buttons = await page.locator('button, input[type="button"], input[type="submit"]').all()
    for btn in buttons:
        try:
            text = await btn.text_content() or await btn.get_attribute('value') or ''
            if text.strip():
                elements.append({
                    'type': 'button',
                    'text': text.strip(),
                    'selector': f'text={text.strip()}'
                })
        except:
            pass
    
    # Links
    links = await page.locator('a[href]').all()
    for link in links:
        try:
            text = await link.text_content()
            href = await link.get_attribute('href')
            if text and text.strip():
                elements.append({
                    'type': 'link',
                    'text': text.strip(),
                    'href': href,
                    'selector': f'text={text.strip()}'
                })
        except:
            pass
    
    # Form fields
    inputs = await page.locator('input[type="text"], input[type="email"], input[type="password"], textarea').all()
    for inp in inputs:
        try:
            name = await inp.get_attribute('name')
            placeholder = await inp.get_attribute('placeholder')
            label = await page.locator(f'label[for="{await inp.get_attribute("id")}"]').text_content() if await inp.get_attribute('id') else None
            
            elements.append({
                'type': 'input',
                'name': name,
                'placeholder': placeholder,
                'label': label,
                'selector': f'[name="{name}"]' if name else f'[placeholder="{placeholder}"]' if placeholder else None
            })
        except:
            pass
    
    return [e for e in elements if e.get('selector')]


def heal_selector(original_selector: str, error_message: str) -> List[str]:
    """Generate alternative selectors when one fails."""
    alternatives = []
    
    # If it was a strict CSS selector, try text-based
    if original_selector.startswith('[') or original_selector.startswith('#') or original_selector.startswith('.'):
        # Extract any visible text hints from error
        if 'text=' in error_message:
            text_match = error_message.split('text=')[1].split(' ')[0].strip('"')
            alternatives.append(f'text={text_match}')
    
    # If it was text-based, try making it less strict
    elif original_selector.startswith('text='):
        text = original_selector[5:].strip('"')
        alternatives.append(f'text=/{text}/i')  # Case insensitive regex
        alternatives.append(f':has-text("{text}")')  # Partial match
        
        # Try common role-based alternatives
        alternatives.extend([
            f'role=button[name="{text}"]',
            f'role=link[name="{text}"]',
            f'[aria-label="{text}"]'
        ])
    
    # Add generic alternatives
    alternatives.extend([
        original_selector + ':visible',  # Only visible elements
        original_selector + ' >> nth=0',  # First match
    ])
    
    return alternatives
