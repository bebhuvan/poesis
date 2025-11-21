#!/usr/bin/env python3
"""
Generate HTML review files for easy human verification of OCR quality.
Includes side-by-side view, confidence scoring, and review checklist.
"""

import json
from pathlib import Path
from typing import List, Dict
import base64

class HTMLReviewGenerator:
    """Generate HTML review files for OCR output."""
    
    def __init__(self):
        self.css = """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                padding: 20px;
                line-height: 1.6;
            }
            
            .header {
                background: white;
                padding: 30px;
                margin-bottom: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            h1 { color: #2c3e50; margin-bottom: 10px; }
            .subtitle { color: #7f8c8d; font-size: 14px; }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            
            .stat-box {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
            }
            
            .stat-value {
                font-size: 32px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            .stat-label {
                font-size: 12px;
                color: #7f8c8d;
                text-transform: uppercase;
                margin-top: 5px;
            }
            
            .review-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .page-section {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .page-title {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #3498db;
            }
            
            .image-container {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .page-image {
                max-width: 100%;
                border: 1px solid #ddd;
                border-radius: 4px;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .page-image:hover {
                transform: scale(1.02);
            }
            
            .text-content {
                white-space: pre-wrap;
                font-family: 'Georgia', serif;
                line-height: 1.8;
                font-size: 14px;
                color: #2c3e50;
                background: #f9f9f9;
                padding: 20px;
                border-radius: 4px;
                border-left: 4px solid #3498db;
                max-height: 600px;
                overflow-y: auto;
            }
            
            .confidence-high { color: #27ae60; }
            .confidence-medium { color: #f39c12; }
            .confidence-low { color: #e74c3c; }
            
            .uncertainty {
                background: #fff3cd;
                border: 2px solid #ffc107;
                padding: 2px 5px;
                border-radius: 3px;
                font-weight: bold;
            }
            
            .checklist {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            
            .checklist h3 {
                color: #2c3e50;
                margin-bottom: 15px;
            }
            
            .checklist-item {
                padding: 10px;
                margin: 5px 0;
                background: #ecf0f1;
                border-radius: 4px;
                display: flex;
                align-items: center;
            }
            
            .checklist-item input {
                margin-right: 10px;
                transform: scale(1.2);
            }
            
            .navigation {
                position: fixed;
                bottom: 20px;
                right: 20px;
                display: flex;
                gap: 10px;
            }
            
            .nav-button {
                padding: 12px 24px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: bold;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                transition: background 0.2s;
            }
            
            .nav-button:hover {
                background: #2980b9;
            }
            
            .nav-button:disabled {
                background: #95a5a6;
                cursor: not-allowed;
            }
            
            .notes-section {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            
            .notes-section textarea {
                width: 100%;
                min-height: 150px;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-family: inherit;
                font-size: 14px;
                resize: vertical;
            }
            
            .notes-section textarea:focus {
                outline: none;
                border-color: #3498db;
            }
            
            @media (max-width: 1200px) {
                .review-container {
                    grid-template-columns: 1fr;
                }
            }
            
            @media print {
                .navigation, .checklist { display: none; }
            }
        </style>
        """
    
    def generate_page_review(self, page_num: int, image_path: Path, 
                            text_content: str, confidence: float,
                            metadata: Dict, output_path: Path):
        """Generate HTML review for a single page."""
        
        # Encode image as base64 for embedding
        if image_path.exists():
            with open(image_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode()
            img_src = f"data:image/png;base64,{img_data}"
        else:
            img_src = ""
        
        # Determine confidence class
        if confidence >= 90:
            conf_class = "confidence-high"
            conf_label = "HIGH"
        elif confidence >= 75:
            conf_class = "confidence-medium"
            conf_label = "MEDIUM"
        else:
            conf_class = "confidence-low"
            conf_label = "LOW"
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR Review - Page {page_num}</title>
    {self.css}
</head>
<body>
    <div class="header">
        <h1>OCR Review - Page {page_num}</h1>
        <div class="subtitle">Nehru's Letters to His Daughter</div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value {conf_class}">{confidence:.1f}%</div>
                <div class="stat-label">OCR Confidence ({conf_label})</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{metadata.get('word_count', 0)}</div>
                <div class="stat-label">Word Count</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{metadata.get('lines', 0)}</div>
                <div class="stat-label">Lines</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{metadata.get('hyphenations', 0)}</div>
                <div class="stat-label">Fixes Applied</div>
            </div>
        </div>
    </div>
    
    <div class="review-container">
        <div class="page-section">
            <div class="page-title">📄 Original Scan</div>
            <div class="image-container">
                <img src="{img_src}" alt="Page {page_num}" class="page-image" 
                     onclick="window.open(this.src)">
            </div>
        </div>
        
        <div class="page-section">
            <div class="page-title">📝 Extracted Text</div>
            <div class="text-content">{self._escape_html(text_content)}</div>
        </div>
    </div>
    
    <div class="checklist">
        <h3>✓ Review Checklist</h3>
        <div class="checklist-item">
            <input type="checkbox" id="check1">
            <label for="check1">Text matches the original scan accurately</label>
        </div>
        <div class="checklist-item">
            <input type="checkbox" id="check2">
            <label for="check2">Paragraph structure is preserved correctly</label>
        </div>
        <div class="checklist-item">
            <input type="checkbox" id="check3">
            <label for="check3">No obvious OCR errors or artifacts</label>
        </div>
        <div class="checklist-item">
            <input type="checkbox" id="check4">
            <label for="check4">Hyphenation is handled appropriately</label>
        </div>
        <div class="checklist-item">
            <input type="checkbox" id="check5">
            <label for="check5">Special formatting (underlines, emphasis) is noted</label>
        </div>
    </div>
    
    <div class="notes-section">
        <h3>📋 Reviewer Notes</h3>
        <textarea placeholder="Add any corrections, observations, or issues here..."></textarea>
    </div>
    
    <div class="navigation">
        <button class="nav-button" onclick="window.location.href='page_{page_num-1:04d}_review.html'" 
                {"disabled" if page_num <= 1 else ""}>← Previous</button>
        <button class="nav-button" onclick="window.location.href='page_{page_num+1:04d}_review.html'">Next →</button>
    </div>
</body>
</html>"""
        
        output_path.write_text(html)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def generate_index(self, pages: List[Dict], output_path: Path):
        """Generate index page for all reviews."""
        
        pages_html = []
        for page in pages:
            page_num = page['page'] + 1
            conf = page.get('confidence', 0)
            conf_class = "confidence-high" if conf >= 90 else "confidence-medium" if conf >= 75 else "confidence-low"
            
            pages_html.append(f"""
                <div class="page-card">
                    <div class="page-number">Page {page_num}</div>
                    <div class="page-stats">
                        <span class="{conf_class}">{conf:.0f}% confidence</span>
                        <span>{page.get('lines', 0)} lines</span>
                    </div>
                    <a href="page_{page_num:04d}_review.html" class="review-link">Review →</a>
                </div>
            """)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OCR Review Index</title>
    {self.css}
    <style>
        .pages-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .page-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        
        .page-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .page-number {{
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .page-stats {{
            display: flex;
            flex-direction: column;
            gap: 5px;
            font-size: 12px;
            color: #7f8c8d;
            margin-bottom: 15px;
        }}
        
        .review-link {{
            display: inline-block;
            padding: 8px 16px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            transition: background 0.2s;
        }}
        
        .review-link:hover {{
            background: #2980b9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 OCR Review Index</h1>
        <div class="subtitle">Nehru's Letters to His Daughter - All Pages</div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(pages)}</div>
                <div class="stat-label">Total Pages</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{sum(p.get('lines', 0) for p in pages)}</div>
                <div class="stat-label">Total Lines</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{sum(p.get('confidence', 0) for p in pages) / len(pages):.1f}%</div>
                <div class="stat-label">Avg Confidence</div>
            </div>
        </div>
    </div>
    
    <div class="pages-grid">
        {''.join(pages_html)}
    </div>
</body>
</html>"""
        
        output_path.write_text(html)


def main():
    """Will be called after processing completes."""
    print("HTML review generator ready")


if __name__ == "__main__":
    main()
