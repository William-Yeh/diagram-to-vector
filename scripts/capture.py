#!/usr/bin/env python3
"""
capture.py
Capture screenshots from whiteboard URLs using Playwright.

Author: William Yeh <william.pjyeh@gmail.com>
License: MIT

Usage:
    python scripts/capture.py <URL> [options]

Options:
    --output, -o <file>     Output filename (default: screenshot.png)
    --zoom, -z <float>      Zoom level (default: 1.0)
    --wait, -w <seconds>    Wait time for content to render (default: 3)
    --region, -r <x,y,w,h>  Capture specific region
    --full-page             Capture full scrollable page
    --no-hide-ui            Keep toolbar/UI visible
    --browser <name>        chromium (default), firefox, webkit
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict


def ensure_playwright_installed() -> bool:
    """Ensure playwright is installed."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        print("Playwright not found. Please install dependencies:")
        print("  uv pip install -r requirements.txt")
        print("  uv run python -m playwright install chromium")
        print("\nOr with pip:")
        print("  pip install playwright")
        print("  python -m playwright install chromium")
        sys.exit(1)


def parse_region(region_str: str) -> Optional[Dict[str, int]]:
    """Parse region string 'x,y,width,height' into clip dict."""
    if not region_str:
        return None
    try:
        parts = [int(x.strip()) for x in region_str.split(',')]
        if len(parts) == 4:
            return {'x': parts[0], 'y': parts[1], 'width': parts[2], 'height': parts[3]}
    except ValueError:
        pass
    print(f"Warning: Invalid region format '{region_str}', expected 'x,y,width,height'")
    return None


def detect_whiteboard_type(url: str) -> str:
    """Detect the type of whiteboard from URL."""
    url_lower = url.lower()
    if 'tldraw.com' in url_lower:
        return 'tldraw'
    elif 'excalidraw.com' in url_lower:
        return 'excalidraw'
    elif 'miro.com' in url_lower:
        return 'miro'
    elif 'figma.com' in url_lower:
        return 'figma'
    elif 'whimsical.com' in url_lower:
        return 'whimsical'
    elif 'lucid' in url_lower:
        return 'lucidchart'
    return 'generic'


def get_ui_selectors(whiteboard_type: str) -> list:
    """Get CSS selectors for UI elements to hide."""
    common = [
        '[class*="toolbar" i]', '[class*="sidebar" i]', '[class*="menu" i]',
        '[class*="panel" i]', '[class*="header" i]', '[class*="footer" i]',
        '[class*="controls" i]', '[role="toolbar"]', '[role="menubar"]',
        'nav', 'aside',
    ]
    
    specific = {
        'tldraw': ['.tlui-layout__top', '.tlui-layout__bottom', '.tlui-navigation-zone'],
        'excalidraw': ['.Island', '.App-menu', '.ToolIcon', '.layer-ui__wrapper'],
        'miro': ['.board-ui', '.toolbar', '.bottomBar'],
        'figma': ['[class*="toolbar"]', '[class*="panel"]'],
    }
    
    return common + specific.get(whiteboard_type, [])


def capture_screenshot(
    url: str,
    output: str = "screenshot.png",
    zoom: float = 1.0,
    wait: int = 3,
    width: int = 1920,
    height: int = 1080,
    region: Optional[str] = None,
    full_page: bool = False,
    hide_ui: bool = True,
    browser: str = "chromium"
) -> str:
    """Capture a screenshot from a whiteboard URL."""
    ensure_playwright_installed()
    from playwright.sync_api import sync_playwright
    
    whiteboard_type = detect_whiteboard_type(url)
    print(f"Detected: {whiteboard_type}")
    print(f"Capturing: {url}")
    
    clip = parse_region(region) if region else None
    
    with sync_playwright() as p:
        browser_type = getattr(p, browser, p.chromium)
        browser_instance = browser_type.launch(headless=True)
        
        context = browser_instance.new_context(
            viewport={'width': int(width * zoom), 'height': int(height * zoom)},
            device_scale_factor=zoom,
            ignore_https_errors=True
        )
        
        page = context.new_page()
        
        print("Loading page...")
        try:
            page.goto(url, wait_until='networkidle', timeout=60000)
        except Exception as e:
            print(f"Warning: {e}")
        
        print(f"Waiting {wait}s...")
        page.wait_for_timeout(wait * 1000)
        
        try:
            page.wait_for_selector('canvas', timeout=5000)
        except Exception:
            pass  # Canvas not found, proceed anyway
        
        if hide_ui:
            selectors = get_ui_selectors(whiteboard_type)
            page.evaluate('''(selectors) => {
                selectors.forEach(s => {
                    document.querySelectorAll(s).forEach(el => {
                        el.style.setProperty('opacity', '0', 'important');
                        el.style.setProperty('visibility', 'hidden', 'important');
                    });
                });
            }''', selectors)
            page.wait_for_timeout(300)
        
        screenshot_opts = {'path': output, 'type': 'png'}
        if clip:
            screenshot_opts['clip'] = clip
        elif full_page:
            screenshot_opts['full_page'] = True
        
        page.screenshot(**screenshot_opts)
        context.close()
        browser_instance.close()
    
    print(f"Saved: {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description='Capture whiteboard screenshots')
    parser.add_argument('url', help='URL to capture')
    parser.add_argument('--output', '-o', default='screenshot.png')
    parser.add_argument('--zoom', '-z', type=float, default=1.0)
    parser.add_argument('--wait', '-w', type=int, default=3)
    parser.add_argument('--region', '-r', help='x,y,width,height')
    parser.add_argument('--full-page', action='store_true')
    parser.add_argument('--no-hide-ui', action='store_true')
    parser.add_argument('--browser', '-b', default='chromium',
                        choices=['chromium', 'firefox', 'webkit'])
    
    args = parser.parse_args()
    
    try:
        capture_screenshot(
            url=args.url, output=args.output, zoom=args.zoom,
            wait=args.wait, region=args.region,
            full_page=args.full_page, hide_ui=not args.no_hide_ui,
            browser=args.browser
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
