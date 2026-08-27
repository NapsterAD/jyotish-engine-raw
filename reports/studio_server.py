"""
studio_server.py — Comprehensive Interactive A4 Export Studio Server for Jyotish Calculation Engine.
Hosts a local web application on http://localhost:8089 to preview, customize, modify birth parameters,
toggle pages, edit styles/content in real-time, and print/export publication-grade A4 reports.
"""

import os
import sys
import json
import urllib.parse
import http.server
import socketserver
import threading
import webbrowser
from typing import Dict, Any, List, Optional

# Ensure project root is in path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jyotish_engine.main import JyotishEngine
from jyotish_engine.reports.generator import ReportGenerator

# Empty studio defaults — never compute a silent Aditya chart.
DEFAULT_PARAMS = {
    "name": "",
    "date": "",
    "time": "",
    "tz": "",
    "lat": "",
    "lon": "",
    "place": "",
    "ayanamsha": "lahiri",
    "chart_style": "north",
    "theme": "gold",
    "selected_pages": list(range(1, 15)),
    "header_title": "JYOTISH KUNDALI MASTER REPORT",
    "subtitle": "Comprehensive Vedic Astrological Analysis",
    "custom_notes": "",
    "watermark": "",
    "custom_css": ""
}

# Optional labelled example only (verification lock). Never used as compute default.
EXAMPLE_NATIVE = {
    "name": "Aditya Prasad",
    "date": "2000-10-06",
    "time": "07:02:21",
    "tz": "+05:30",
    "lat": 23.797487,
    "lon": 86.305251,
    "place": "Katrasgarh, Jharkhand, India",
    "ayanamsha": "lahiri",
}

PAGE_NAMES = {
    1: "Core Chart, Panchanga & Planetary Sphutas",
    2: "Bhava Chalit, House Cusps & Arudha Padas",
    3: "Ashtakavarga Matrix (SAV/BAV) & Shadbala",
    4: "Vimshottari Dasha Hierarchy & Yogini Dasha",
    5: "Major Yogas, Doshas & Divisional Vargas (D-10)",
    6: "KP Placidus Cusps & ABCD Significators",
    7: "Rasi Dashas (Narayana, Chara, Kalachakra)",
    8: "Transits, Sade Sati & Double Transit",
    9: "Lal Kitab Debts/Remedies & Bhrigu Nandi",
    10: "Sensitive Points, Pushkara & Mrityu Bhaga",
    11: "Raw Sthana Sub-scores & BAV Matrix",
    12: "Varga Sphutas & Nakshatra 249 Sub-Lords",
    13: "10-Year Planetary Ingress Timelines",
    14: "Deep Multi-Tier Dasha Trees (MD → AD → PD)"
}


def build_studio_html() -> str:
    """Generate the single-page application HTML for the A4 Export Studio."""
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Jyotish Kundali · A4 Export Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-app: #090d16;
      --bg-panel: #0f172a;
      --bg-card: #1e293b;
      --bg-input: #0b1120;
      --border-panel: #334155;
      --border-focus: #f59e0b;
      --accent-gold: #f59e0b;
      --accent-amber: #d97706;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --success: #10b981;
      --danger: #ef4444;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-serif: 'Cinzel', Georgia, serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: var(--font-sans);
      background-color: var(--bg-app);
      color: var(--text-main);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* ─── Top Studio Navigation Bar ─── */
    .studio-header {
      height: 56px;
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-panel);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      z-index: 100;
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-logo {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #f59e0b, #b45309);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #0f172a;
      box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
    }

    .brand-title {
      font-family: var(--font-serif);
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #ffffff;
    }

    .brand-title span {
      color: var(--accent-gold);
    }

    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--success);
      font-size: 0.72rem;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 9999px;
    }

    .status-dot {
      width: 6px;
      height: 6px;
      background: var(--success);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--success);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    /* ─── Buttons ─── */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      border: 1px solid transparent;
      text-decoration: none;
      user-select: none;
    }

    .btn-primary {
      background: linear-gradient(135deg, #d97706, #b45309);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(217, 119, 6, 0.35);
    }
    .btn-primary:hover {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.45);
    }

    .btn-secondary {
      background: var(--bg-card);
      border-color: var(--border-panel);
      color: var(--text-main);
    }
    .btn-secondary:hover {
      background: #334155;
      border-color: #475569;
    }

    .btn-success {
      background: rgba(16, 185, 129, 0.15);
      border-color: rgba(16, 185, 129, 0.4);
      color: #34d399;
    }
    .btn-success:hover {
      background: rgba(16, 185, 129, 0.25);
    }

    /* ─── Main Workspace Split ─── */
    .studio-workspace {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    /* ─── Left Sidebar Studio Panel ─── */
    .studio-sidebar {
      width: 440px;
      min-width: 360px;
      background: var(--bg-panel);
      border-right: 1px solid var(--border-panel);
      display: flex;
      flex-direction: column;
      height: calc(100vh - 56px);
      transition: width 0.2s ease;
    }

    /* ─── Sidebar Navigation Tabs ─── */
    .sidebar-tabs {
      display: flex;
      background: var(--bg-input);
      border-bottom: 1px solid var(--border-panel);
      overflow-x: auto;
    }

    .tab-btn {
      flex: 1;
      padding: 11px 8px;
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      white-space: nowrap;
      transition: all 0.15s ease;
    }

    .tab-btn:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.02);
    }

    .tab-btn.active {
      color: var(--accent-gold);
      border-bottom-color: var(--accent-gold);
      background: rgba(245, 158, 11, 0.06);
    }

    /* ─── Tab Content Scrollable Area ─── */
    .tab-content-area {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
    }

    .tab-pane {
      display: none;
      flex-direction: column;
      gap: 16px;
    }

    .tab-pane.active {
      display: flex;
    }

    /* ─── Form Controls & Group Styling ─── */
    .control-group {
      background: var(--bg-card);
      border: 1px solid var(--border-panel);
      border-radius: 8px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .group-title {
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--accent-gold);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .form-field {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .form-field.full {
      grid-column: 1 / -1;
    }

    label {
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--text-muted);
      letter-spacing: 0.3px;
    }

    input[type="text"],
    input[type="date"],
    input[type="time"],
    input[type="number"],
    select,
    textarea {
      background: var(--bg-input);
      border: 1px solid var(--border-panel);
      border-radius: 6px;
      padding: 8px 10px;
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 0.82rem;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
      width: 100%;
    }

    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: var(--accent-gold);
      box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
    }

    textarea {
      resize: vertical;
      min-height: 80px;
      font-family: var(--font-sans);
      line-height: 1.4;
    }

    .code-editor {
      font-family: var(--font-mono);
      font-size: 0.76rem;
      min-height: 220px;
      line-height: 1.45;
      background: #050811;
      color: #e2e8f0;
      tab-size: 2;
    }

    /* ─── Pages Checklist ─── */
    .page-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-height: 380px;
      overflow-y: auto;
      padding-right: 4px;
    }

    .page-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 10px;
      background: var(--bg-input);
      border: 1px solid var(--border-panel);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .page-item:hover {
      border-color: #475569;
      background: #172033;
    }

    .page-item input[type="checkbox"] {
      accent-color: var(--accent-gold);
      width: 15px;
      height: 15px;
      cursor: pointer;
    }

    .page-badge {
      font-family: var(--font-mono);
      font-size: 0.7rem;
      font-weight: 700;
      background: rgba(245, 158, 11, 0.15);
      color: var(--accent-gold);
      padding: 2px 6px;
      border-radius: 4px;
    }

    .page-label {
      font-size: 0.78rem;
      font-weight: 500;
      color: var(--text-main);
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .quick-pill-group {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }

    .pill-btn {
      font-size: 0.72rem;
      padding: 4px 8px;
      background: var(--bg-input);
      border: 1px solid var(--border-panel);
      color: var(--text-muted);
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .pill-btn:hover {
      color: var(--accent-gold);
      border-color: var(--accent-gold);
    }

    /* ─── Sidebar Footer Action ─── */
    .sidebar-footer {
      padding: 12px 16px;
      background: var(--bg-input);
      border-top: 1px solid var(--border-panel);
      display: flex;
      gap: 10px;
    }

    /* ─── Right Canvas / Preview Viewport ─── */
    .studio-preview-area {
      flex: 1;
      background: #020617;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
    }

    /* ─── Preview Control Sub-Header ─── */
    .preview-bar {
      height: 48px;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid var(--border-panel);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      z-index: 10;
    }

    .zoom-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .zoom-btn {
      width: 26px;
      height: 26px;
      background: var(--bg-card);
      border: 1px solid var(--border-panel);
      color: var(--text-main);
      border-radius: 4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
    }

    .zoom-val {
      font-family: var(--font-mono);
      font-size: 0.76rem;
      color: var(--text-muted);
      min-width: 44px;
      text-align: center;
    }

    .page-nav-chips {
      display: flex;
      align-items: center;
      gap: 5px;
      overflow-x: auto;
      max-width: 50vw;
      padding: 2px 0;
    }

    .page-chip {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 3px 8px;
      background: var(--bg-card);
      border: 1px solid var(--border-panel);
      color: var(--text-muted);
      border-radius: 4px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }

    .page-chip:hover, .page-chip.active {
      background: var(--accent-amber);
      color: #ffffff;
      border-color: var(--accent-gold);
    }

    /* ─── Preview Container / Iframe ─── */
    .preview-viewport {
      flex: 1;
      overflow: auto;
      padding: 24px 12px;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      background: radial-gradient(circle at 50% 30%, #1e293b 0%, #090d16 100%);
    }

    .preview-frame-wrapper {
      transition: transform 0.15s ease;
      transform-origin: top center;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.75);
      border-radius: 4px;
      overflow: visible;
    }

    #reportFrame {
      border: none;
      width: 210mm;
      min-height: 297mm;
      background: #ffffff;
      border-radius: 2px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      display: block;
    }

    /* ─── Loading Overlay ─── */
    .loading-overlay {
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(9, 13, 22, 0.7);
      backdrop-filter: blur(4px);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      z-index: 50;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease;
    }

    .loading-overlay.visible {
      opacity: 1;
      pointer-events: auto;
    }

    .spinner {
      width: 36px;
      height: 36px;
      border: 3px solid rgba(245, 158, 11, 0.2);
      border-top-color: var(--accent-gold);
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    /* ─── Toast Notifications ─── */
    .toast-container {
      position: fixed;
      bottom: 20px;
      right: 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      z-index: 999;
    }

    .toast {
      background: #1e293b;
      border: 1px solid var(--border-panel);
      color: var(--text-main);
      padding: 10px 16px;
      border-radius: 6px;
      font-size: 0.8rem;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      gap: 8px;
      animation: slideIn 0.2s ease;
    }

    .toast.success { border-color: var(--success); color: #34d399; }
    .toast.error { border-color: var(--danger); color: #f87171; }

    @keyframes slideIn {
      from { transform: translateY(12px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  </style>
</head>
<body>

  <!-- Top Studio Header -->
  <header class="studio-header">
    <div class="brand-group">
      <div class="brand-logo">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="12" cy="12" r="10"/>
          <polygon points="12 2 15 8 22 9 17 14 18 21 12 17 6 21 7 14 2 9 9 8 12 2"/>
        </svg>
      </div>
      <div class="brand-title">JYOTISH <span>A4 STUDIO</span></div>
      <div class="status-badge">
        <div class="status-dot"></div>
        <span>Live Engine · ISO A4</span>
      </div>
    </div>

    <div class="header-actions">
      <button class="btn btn-secondary" onclick="toggleEditMode()" id="editModeToggleBtn" title="Directly click and edit text on report pages">
        ✏️ In-Place Edit
      </button>
      <button class="btn btn-secondary" onclick="downloadHtmlReport()" title="Download standalone single-file HTML report">
        📥 HTML Export
      </button>
      <button class="btn btn-primary" onclick="printReport()" title="Print or Save PDF using exact A4 ISO specifications">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <polyline points="6 9 6 2 18 2 18 9"/>
          <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
          <rect x="6" y="14" width="12" height="8"/>
        </svg>
        Print / Save A4 PDF
      </button>
    </div>
  </header>

  <!-- Main Workspace -->
  <div class="studio-workspace">

    <!-- Left Control Studio Sidebar -->
    <aside class="studio-sidebar">
      
      <!-- Sidebar Navigation Tabs -->
      <nav class="sidebar-tabs">
        <button class="tab-btn active" onclick="switchTab('tab-birth')">🔮 Birth Data</button>
        <button class="tab-btn" onclick="switchTab('tab-pages')">📑 Pages (14)</button>
        <button class="tab-btn" onclick="switchTab('tab-content')">✍️ Text & Notes</button>
        <button class="tab-btn" onclick="switchTab('tab-styles')">🎨 Styling & CSS</button>
        <button class="tab-btn" onclick="switchTab('tab-json')">📊 Raw JSON</button>
      </nav>

      <!-- Scrollable Tab Content Container -->
      <div class="tab-content-area">

        <!-- TAB 1: Birth Data & Astronomical Parameters -->
        <div class="tab-pane active" id="tab-birth">
          <div class="control-group">
            <div class="group-title">
              <span>Native Profile</span>
              <div style="display:flex;gap:6px;">
                <button class="pill-btn" onclick="clearNativeForm()">Clear</button>
                <button class="pill-btn" onclick="loadExampleNative()">Load example</button>
              </div>
            </div>
            <div class="form-field full">
              <label for="nativeName">Full Name</label>
              <input type="text" id="nativeName" value="" placeholder="e.g. Full name">
            </div>
            <div class="form-row">
              <div class="form-field">
                <label for="birthDate">Date of Birth</label>
                <input type="date" id="birthDate" value="">
              </div>
              <div class="form-field">
                <label for="birthTime">Time (HH:MM:SS)</label>
                <input type="text" id="birthTime" value="" placeholder="07:02:21">
              </div>
            </div>
            <div class="form-row">
              <div class="form-field">
                <label for="birthTz">Timezone</label>
                <input type="text" id="birthTz" value="" placeholder="+05:30 or America/New_York">
              </div>
              <div class="form-field">
                <label for="birthPlace">Place Name</label>
                <input type="text" id="birthPlace" value="" placeholder="City, region, country">
              </div>
            </div>
            <div class="form-row">
              <div class="form-field">
                <label for="birthLat">Latitude (°N)</label>
                <input type="number" step="0.000001" id="birthLat" value="" placeholder="e.g. 23.797487">
              </div>
              <div class="form-field">
                <label for="birthLon">Longitude (°E)</label>
                <input type="number" step="0.000001" id="birthLon" value="" placeholder="e.g. 86.305251">
              </div>
            </div>
          </div>

          <div class="control-group">
            <div class="group-title">Astrological Engine Settings</div>
            <div class="form-row">
              <div class="form-field">
                <label for="ayanamshaSelect">Ayanamsha</label>
                <select id="ayanamshaSelect">
                  <option value="lahiri" selected>Lahiri (Chitrapaksha)</option>
                  <option value="raman">B.V. Raman</option>
                  <option value="krishnamurti">Krishnamurti (KP)</option>
                  <option value="tropical">Sayana (Tropical)</option>
                  <option value="fagan_bradley">Fagan-Bradley</option>
                  <option value="yukteshwar">Sri Yukteshwar</option>
                </select>
              </div>
              <div class="form-field">
                <label for="chartStyleSelect">Chart Style</label>
                <select id="chartStyleSelect">
                  <option value="north" selected>North Indian (Diamond)</option>
                  <option value="south">South Indian (Square)</option>
                </select>
              </div>
            </div>
            <div class="form-field full">
              <label for="themeSelect">Color Theme Palette</label>
              <select id="themeSelect">
                <option value="gold" selected>👑 Imperial Vedic Gold (Navy + Gold)</option>
                <option value="navy">🌌 Midnight Navy (Deep Indigo + Cyan)</option>
                <option value="monochrome">📜 Classical Monochrome (B&W High Contrast)</option>
                <option value="ruby">🍷 Royal Ruby (Burgundy + Rose Gold)</option>
                <option value="emerald">🌿 Vedic Emerald (Spruce + Imperial Bronze)</option>
                <option value="sapphire">💎 Regal Sapphire (Deep Indigo + Violet)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- TAB 2: Pages & Section Manager -->
        <div class="tab-pane" id="tab-pages">
          <div class="control-group">
            <div class="group-title">
              <span>Page Presets</span>
            </div>
            <div class="quick-pill-group">
              <button class="pill-btn" onclick="selectPreset('all')">🌟 All 14 Pages</button>
              <button class="pill-btn" onclick="selectPreset('standard')">📑 Standard 10 Pages</button>
              <button class="pill-btn" onclick="selectPreset('core')">📖 Classical 5 Pages</button>
              <button class="pill-btn" onclick="selectPreset('summary')">⚡ 1-Page Summary</button>
              <button class="pill-btn" onclick="toggleAllPages(false)">❌ Clear All</button>
            </div>
          </div>

          <div class="control-group">
            <div class="group-title">
              <span>Included Report Pages</span>
              <span id="pageCountBadge" style="font-size: 0.72rem; color: var(--text-muted);">14 / 14 selected</span>
            </div>
            <div class="page-list" id="pageCheckboxList">
              <!-- Dynamically populated -->
            </div>
          </div>
        </div>

        <!-- TAB 3: Text & Notes Customizer -->
        <div class="tab-pane" id="tab-content">
          <div class="control-group">
            <div class="group-title">Report Titles & Branding</div>
            <div class="form-field full">
              <label for="headerTitle">Main Document Title</label>
              <input type="text" id="headerTitle" value="JYOTISH KUNDALI MASTER REPORT">
            </div>
            <div class="form-field full">
              <label for="subTitle">Subtitle / Badge</label>
              <input type="text" id="subTitle" value="Comprehensive Vedic Astrological Analysis">
            </div>
            <div class="form-field full">
              <label for="watermarkText">Document Watermark (Optional)</label>
              <input type="text" id="watermarkText" placeholder="e.g. CONFIDENTIAL or DRAFT">
            </div>
          </div>

          <div class="control-group">
            <div class="group-title">Consultation Notes / Remarks</div>
            <div class="form-field full">
              <label for="customNotes">Custom Astrological Notes</label>
              <textarea id="customNotes" placeholder="Write custom astrological synthesis, predictions, or remedies to include in report output..."></textarea>
            </div>
          </div>
        </div>

        <!-- TAB 4: Visual Styling & CSS Editor -->
        <div class="tab-pane" id="tab-styles">
          <div class="control-group">
            <div class="group-title">Live CSS Code Editor</div>
            <p style="font-size: 0.72rem; color: var(--text-muted);">
              Add custom CSS rules or overrides below. Changes apply instantly to preview.
            </p>
            <textarea id="customCssCode" class="code-editor" spellcheck="false" placeholder="/* Custom CSS overrides */
body {
  /* --color-accent-gold: #eab308; */
}
.a4-page {
  /* zoom: 1.0; */
}"></textarea>
            <div style="display: flex; gap: 8px; justify-content: flex-end;">
              <button class="btn btn-secondary" onclick="loadBaseCss()">Load Current report_a4.css</button>
              <button class="btn btn-primary" onclick="saveCssToDisk()">Save to Disk</button>
            </div>
          </div>
        </div>

        <!-- TAB 5: Raw Calculations & JSON Inspector -->
        <div class="tab-pane" id="tab-json">
          <div class="control-group">
            <div class="group-title">
              <span>Calculated JSON Data</span>
              <div style="display: flex; gap: 6px;">
                <button class="pill-btn" onclick="copyJsonData()">📋 Copy</button>
                <button class="pill-btn" onclick="downloadJsonData()">📥 Download</button>
              </div>
            </div>
            <textarea id="rawJsonViewer" class="code-editor" readonly style="min-height: 380px;"></textarea>
          </div>
        </div>

      </div>

      <!-- Sidebar Footer Action -->
      <footer class="sidebar-footer">
        <button class="btn btn-primary" style="flex: 1;" onclick="triggerRecompute()">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
          Re-Render Report Preview
        </button>
        <button class="btn btn-secondary" onclick="saveReportToDisk()" title="Save HTML to jyotish_engine/output/">
          💾 Save
        </button>
      </footer>
    </aside>

    <!-- Right Live A4 Preview Viewport -->
    <main class="studio-preview-area">
      
      <!-- Sub-Bar for Zoom & Quick Jump -->
      <div class="preview-bar">
        <div class="zoom-controls">
          <button class="zoom-btn" onclick="adjustZoom(-10)">−</button>
          <span class="zoom-val" id="zoomDisplay">100%</span>
          <button class="zoom-btn" onclick="adjustZoom(10)">+</button>
          <button class="pill-btn" onclick="setZoom(75)">75%</button>
          <button class="pill-btn" onclick="setZoom(100)">100%</button>
          <button class="pill-btn" onclick="setZoom(125)">125%</button>
        </div>

        <div class="page-nav-chips" id="pageNavChips">
          <!-- Page chips rendered here -->
        </div>

        <div>
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 0.75rem;" onclick="openStandaloneReport()">
            ↗ Open in New Tab
          </button>
        </div>
      </div>

      <!-- Preview Viewport Container -->
      <div class="preview-viewport" id="previewViewport">
        <div class="preview-frame-wrapper" id="frameWrapper">
          <iframe id="reportFrame" title="A4 Report Preview"></iframe>
        </div>
      </div>

      <!-- Loading Spinner Overlay -->
      <div class="loading-overlay" id="loadingOverlay">
        <div class="spinner"></div>
        <span style="font-size: 0.85rem; font-weight: 600; color: var(--accent-gold);">Computing & Rendering A4 Report...</span>
      </div>

    </main>

  </div>

  <!-- Toast Notification Container -->
  <div class="toast-container" id="toastContainer"></div>

  <script>
    const PAGE_NAMES = {
      1: "Core Chart, Panchanga & Planetary Sphutas",
      2: "Bhava Chalit, House Cusps & Arudha Padas",
      3: "Ashtakavarga Matrix (SAV/BAV) & Shadbala",
      4: "Vimshottari Dasha Hierarchy & Yogini Dasha",
      5: "Major Yogas, Doshas & Divisional Vargas (D-10)",
      6: "KP Placidus Cusps & ABCD Significators",
      7: "Rasi Dashas (Narayana, Chara, Kalachakra)",
      8: "Transits, Sade Sati & Double Transit",
      9: "Lal Kitab Debts/Remedies & Bhrigu Nandi",
      10: "Sensitive Points, Pushkara & Mrityu Bhaga",
      11: "Raw Sthana Sub-scores & BAV Matrix",
      12: "Varga Sphutas & Nakshatra 249 Sub-Lords",
      13: "10-Year Planetary Ingress Timelines",
      14: "Deep Multi-Tier Dasha Trees (MD → AD → PD)"
    };

    let currentZoom = 100;
    let isEditingMode = false;
    let latestHtml = "";
    let latestCalculations = {};

    // Initialize UI on load — do not compute until birth fields are filled.
    window.addEventListener('DOMContentLoaded', () => {
      initPageCheckboxes();
      loadBaseCss();
    });

    function initPageCheckboxes() {
      const container = document.getElementById('pageCheckboxList');
      container.innerHTML = '';
      for (let i = 1; i <= 14; i++) {
        const item = document.createElement('label');
        item.className = 'page-item';
        item.innerHTML = `
          <input type="checkbox" value="${i}" checked onchange="updatePageBadge()">
          <span class="page-badge">P${i}</span>
          <span class="page-label">${PAGE_NAMES[i]}</span>
        `;
        container.appendChild(item);
      }
      updatePageBadge();
    }

    function updatePageBadge() {
      const selected = getSelectedPages();
      document.getElementById('pageCountBadge').innerText = `${selected.length} / 14 selected`;
      updatePageNavChips(selected);
    }

    function getSelectedPages() {
      const cbs = document.querySelectorAll('#pageCheckboxList input[type="checkbox"]:checked');
      return Array.from(cbs).map(cb => parseInt(cb.value, 10));
    }

    function selectPreset(preset) {
      const cbs = document.querySelectorAll('#pageCheckboxList input[type="checkbox"]');
      let targetPages = [];
      if (preset === 'all') targetPages = Array.from({length: 14}, (_, i) => i + 1);
      else if (preset === 'standard') targetPages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
      else if (preset === 'core') targetPages = [1, 2, 3, 4, 5];
      else if (preset === 'summary') targetPages = [1];

      cbs.forEach(cb => {
        cb.checked = targetPages.includes(parseInt(cb.value, 10));
      });
      updatePageBadge();
      if (birthFieldsComplete()) triggerRecompute();
    }

    function toggleAllPages(state) {
      document.querySelectorAll('#pageCheckboxList input[type="checkbox"]').forEach(cb => cb.checked = state);
      updatePageBadge();
    }

    function updatePageNavChips(selectedPages) {
      const chipContainer = document.getElementById('pageNavChips');
      chipContainer.innerHTML = '';
      selectedPages.forEach((pnum, idx) => {
        const btn = document.createElement('button');
        btn.className = 'page-chip';
        btn.innerText = `P${pnum}`;
        btn.title = `Jump to ${PAGE_NAMES[pnum]}`;
        btn.onclick = () => jumpToPage(idx);
        chipContainer.appendChild(btn);
      });
    }

    function jumpToPage(pageIndex) {
      const frame = document.getElementById('reportFrame');
      if (frame && frame.contentWindow) {
        const pages = frame.contentDocument.querySelectorAll('.a4-page');
        if (pages[pageIndex]) {
          pages[pageIndex].scrollIntoView({ behavior: 'smooth' });
        }
      }
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
      event.currentTarget.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    }

    function fieldValue(id) {
      const el = document.getElementById(id);
      return el ? String(el.value || '').trim() : '';
    }

    function birthFieldsComplete() {
      return ['birthDate', 'birthTime', 'birthTz', 'birthLat', 'birthLon']
        .every(id => fieldValue(id) !== '');
    }

    function getFormData() {
      const latRaw = fieldValue('birthLat');
      const lonRaw = fieldValue('birthLon');
      return {
        name: document.getElementById('nativeName').value,
        date: document.getElementById('birthDate').value,
        time: document.getElementById('birthTime').value,
        tz: document.getElementById('birthTz').value,
        lat: latRaw === '' ? '' : parseFloat(latRaw),
        lon: lonRaw === '' ? '' : parseFloat(lonRaw),
        place: document.getElementById('birthPlace').value,
        ayanamsha: document.getElementById('ayanamshaSelect').value,
        chart_style: document.getElementById('chartStyleSelect').value,
        theme: document.getElementById('themeSelect').value,
        selected_pages: getSelectedPages(),
        header_title: document.getElementById('headerTitle').value,
        subtitle: document.getElementById('subTitle').value,
        watermark: document.getElementById('watermarkText').value,
        custom_notes: document.getElementById('customNotes').value,
        custom_css: document.getElementById('customCssCode').value
      };
    }

    async function triggerRecompute() {
      if (!birthFieldsComplete()) {
        showToast('Enter date, time, timezone, latitude and longitude first', 'error');
        return;
      }
      const overlay = document.getElementById('loadingOverlay');
      overlay.classList.add('visible');
      const payload = getFormData();

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          latestHtml = data.html;
          const frame = document.getElementById('reportFrame');
          frame.srcdoc = data.html;
          frame.onload = () => {
            adjustFrameHeight();
            if (isEditingMode) setIframeEditable(true);
          };
          fetchChartJson(payload);
          showToast('Report updated successfully', 'success');
        } else {
          showToast('Calculation error: ' + data.error, 'error');
        }
      } catch (err) {
        showToast('Network error during calculation', 'error');
        console.error(err);
      } finally {
        overlay.classList.remove('visible');
      }
    }

    function adjustFrameHeight() {
      const frame = document.getElementById('reportFrame');
      if (frame && frame.contentDocument && frame.contentDocument.body) {
        const h = frame.contentDocument.body.scrollHeight;
        frame.style.height = (h + 60) + 'px';
      }
    }

    async function fetchChartJson(payload) {
      try {
        const res = await fetch('/api/chart-data', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        latestCalculations = data;
        document.getElementById('rawJsonViewer').value = JSON.stringify(data, null, 2);
      } catch (e) {
        console.error("Failed to load calculation JSON", e);
      }
    }

    async function loadBaseCss() {
      try {
        const res = await fetch('/api/css');
        const text = await res.text();
        document.getElementById('customCssCode').value = text;
      } catch (e) {
        console.error(e);
      }
    }

    async function saveCssToDisk() {
      const css = document.getElementById('customCssCode').value;
      try {
        const res = await fetch('/api/save-css', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ css })
        });
        const result = await res.json();
        if (result.success) {
          showToast('CSS saved to report_a4.css successfully', 'success');
          triggerRecompute();
        } else {
          showToast('Failed to save CSS: ' + result.error, 'error');
        }
      } catch (e) {
        showToast('Error saving CSS', 'error');
      }
    }

    function toggleEditMode() {
      isEditingMode = !isEditingMode;
      setIframeEditable(isEditingMode);
      const btn = document.getElementById('editModeToggleBtn');
      if (btn) {
        btn.style.background = isEditingMode ? '#10b981' : '';
        btn.style.color = isEditingMode ? '#ffffff' : '';
        btn.innerText = isEditingMode ? '✅ In-Place Editing ON' : '✏️ In-Place Edit';
      }
      showToast(isEditingMode ? 'In-place edit mode enabled. Click on any text in the preview to edit!' : 'In-place edit mode disabled', 'success');
    }

    function setIframeEditable(editable) {
      const frame = document.getElementById('reportFrame');
      if (frame && frame.contentDocument) {
        const container = frame.contentDocument.getElementById('reportPages');
        if (container) {
          container.setAttribute('contenteditable', editable ? 'true' : 'false');
        }
      }
    }

    function adjustZoom(delta) {
      setZoom(Math.max(40, Math.min(180, currentZoom + delta)));
    }

    function setZoom(val) {
      currentZoom = val;
      document.getElementById('zoomDisplay').innerText = val + '%';
      const wrapper = document.getElementById('frameWrapper');
      wrapper.style.transform = `scale(${val / 100})`;
      wrapper.style.transformOrigin = 'top center';
    }

    function printReport() {
      const frame = document.getElementById('reportFrame');
      if (frame && frame.contentWindow) {
        frame.contentWindow.focus();
        frame.contentWindow.print();
      }
    }

    function downloadHtmlReport() {
      const frame = document.getElementById('reportFrame');
      const docHtml = frame && frame.contentDocument ? frame.contentDocument.documentElement.outerHTML : latestHtml;
      const blob = new Blob([docHtml], { type: 'text/html;charset=utf-8' });
      const link = document.createElement('a');
      const name = document.getElementById('nativeName').value.replace(/\s+/g, '_');
      link.href = URL.createObjectURL(blob);
      link.download = `${name}_A4_Report.html`;
      link.click();
      showToast('Downloaded HTML report', 'success');
    }

    async function saveReportToDisk() {
      const payload = getFormData();
      const frame = document.getElementById('reportFrame');
      payload.html = frame && frame.contentDocument ? frame.contentDocument.documentElement.outerHTML : latestHtml;

      try {
        const res = await fetch('/api/save-disk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          showToast(`Saved to ${data.file}`, 'success');
        } else {
          showToast(`Save failed: ${data.error}`, 'error');
        }
      } catch (e) {
        showToast('Error saving file to disk', 'error');
      }
    }

    function copyJsonData() {
      const text = document.getElementById('rawJsonViewer').value;
      navigator.clipboard.writeText(text);
      showToast('Calculations JSON copied to clipboard', 'success');
    }

    function downloadJsonData() {
      const text = document.getElementById('rawJsonViewer').value;
      const blob = new Blob([text], { type: 'application/json' });
      const link = document.createElement('a');
      const name = document.getElementById('nativeName').value.replace(/\s+/g, '_');
      link.href = URL.createObjectURL(blob);
      link.download = `${name}_astrological_data.json`;
      link.click();
    }

    function openStandaloneReport() {
      const w = window.open();
      w.document.write(latestHtml);
      w.document.close();
    }

    function clearNativeForm() {
      document.getElementById('nativeName').value = "";
      document.getElementById('birthDate').value = "";
      document.getElementById('birthTime').value = "";
      document.getElementById('birthTz').value = "";
      document.getElementById('birthLat').value = "";
      document.getElementById('birthLon').value = "";
      document.getElementById('birthPlace').value = "";
      document.getElementById('ayanamshaSelect').value = "lahiri";
      showToast('Birth fields cleared', 'success');
    }

    function loadExampleNative() {
      document.getElementById('nativeName').value = "Aditya Prasad";
      document.getElementById('birthDate').value = "2000-10-06";
      document.getElementById('birthTime').value = "07:02:21";
      document.getElementById('birthTz').value = "+05:30";
      document.getElementById('birthLat').value = 23.797487;
      document.getElementById('birthLon').value = 86.305251;
      document.getElementById('birthPlace').value = "Katrasgarh, Jharkhand, India";
      document.getElementById('ayanamshaSelect').value = "lahiri";
      showToast('Loaded example native (verification lock only)', 'success');
    }

    function showToast(msg, type = 'info') {
      const container = document.getElementById('toastContainer');
      const toast = document.createElement('div');
      toast.className = `toast ${type}`;
      toast.innerText = msg;
      container.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 200);
      }, 3200);
    }
  </script>
</body>
</html>
"""


class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving A4 Studio UI and REST API."""

    def __init__(self, *args, **kwargs):
        self.css_path = os.path.join(ROOT, "jyotish_engine", "templates", "styles", "report_a4.css")
        self.output_dir = os.path.join(ROOT, "jyotish_engine", "output")
        os.makedirs(self.output_dir, exist_ok=True)
        super().__init__(*args, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, content_type: str = "text/plain", status: int = 200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html", "/studio"):
            self._send_html(build_studio_html())
            return

        elif path == "/api/default-params":
            self._send_json(DEFAULT_PARAMS)
            return

        elif path == "/api/example-params":
            self._send_json(EXAMPLE_NATIVE)
            return

        elif path == "/api/css":
            if os.path.exists(self.css_path):
                with open(self.css_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = "/* CSS not found */"
            self._send_text(content, content_type="text/css")
            return

        elif path == "/api/output-files":
            files = []
            if os.path.isdir(self.output_dir):
                for f in sorted(os.listdir(self.output_dir)):
                    fp = os.path.join(self.output_dir, f)
                    files.append({
                        "name": f,
                        "size": os.path.getsize(fp),
                        "mtime": os.path.getmtime(fp)
                    })
            self._send_json({"files": files})
            return

        elif path.startswith("/styles/report_a4.css"):
            if os.path.exists(self.css_path):
                with open(self.css_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self._send_text(content, content_type="text/css")
                return

        # Fallback to standard handler
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        
        try:
            payload = json.loads(raw_body)
        except Exception:
            payload = {}

        if path == "/api/generate":
            try:
                missing = [k for k in ("date", "time", "tz", "lat", "lon") if payload.get(k) in (None, "")]
                if missing:
                    raise ValueError("missing birth fields: " + ", ".join(missing))
                date = payload["date"]
                time = payload["time"]
                tz = payload["tz"]
                lat = float(payload["lat"])
                lon = float(payload["lon"])
                name = payload.get("name") or ""
                place = payload.get("place", "")
                ayanamsha = payload.get("ayanamsha", "lahiri")
                chart_style = payload.get("chart_style", "north")
                theme = payload.get("theme", "gold")
                selected_pages = payload.get("selected_pages", list(range(1, 15)))
                header_title = payload.get("header_title")
                subtitle = payload.get("subtitle")
                custom_notes = payload.get("custom_notes")
                watermark = payload.get("watermark")
                custom_css = payload.get("custom_css")

                engine = JyotishEngine(ayanamsha=ayanamsha)
                chart = engine.compute(date=date, time=time, tz=tz, lat=lat, lon=lon, name=name)
                if place:
                    chart.birth_data["place"] = place

                gen = ReportGenerator()
                html = gen.generate_html(
                    chart,
                    chart_style=chart_style,
                    theme=theme,
                    selected_pages=selected_pages,
                    custom_css=custom_css,
                    header_title=header_title,
                    subtitle=subtitle,
                    custom_notes=custom_notes,
                    include_toolbar=True,
                    watermark=watermark
                )

                self._send_json({
                    "success": True,
                    "html": html,
                    "page_count": len(selected_pages),
                    "name": name
                })
            except Exception as e:
                import traceback
                self._send_json({"success": False, "error": str(e), "trace": traceback.format_exc()}, status=500)
            return

        elif path == "/api/chart-data":
            try:
                missing = [k for k in ("date", "time", "tz", "lat", "lon") if payload.get(k) in (None, "")]
                if missing:
                    raise ValueError("missing birth fields: " + ", ".join(missing))
                date = payload["date"]
                time = payload["time"]
                tz = payload["tz"]
                lat = float(payload["lat"])
                lon = float(payload["lon"])
                name = payload.get("name") or ""
                ayanamsha = payload.get("ayanamsha", "lahiri")

                engine = JyotishEngine(ayanamsha=ayanamsha)
                chart = engine.compute(date=date, time=time, tz=tz, lat=lat, lon=lon, name=name)

                summary = {
                    "native": chart.birth_data,
                    "lagna": chart.lagna_sign,
                    "positions": {
                        p: {
                            "sign": pos.get("sign"),
                            "dms": pos.get("dms"),
                            "nakshatra": pos.get("nakshatra"),
                            "pada": pos.get("pada"),
                            "retrograde": pos.get("retrograde")
                        }
                        for p, pos in chart.positions.items() if not p.startswith("_")
                    },
                    "panchang": chart.panchang,
                    "ashtakavarga_sav": chart.ashtakavarga.get("sav") if chart.ashtakavarga else None,
                    "shadbala": {
                        p: {
                            "total_rupa": (chart.shadbala.get(p) or {}).get("total_rupa"),
                            "rank": (chart.shadbala.get(p) or {}).get("rank")
                        }
                        for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
                    } if chart.shadbala else None,
                    "yogas": chart.yogas
                }
                self._send_json(summary)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/save-css":
            try:
                css_content = payload.get("css", "")
                with open(self.css_path, "w", encoding="utf-8") as f:
                    f.write(css_content)
                self._send_json({"success": True})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        elif path == "/api/save-disk":
            try:
                name = payload.get("name", "Kundali").replace(" ", "_")
                html_content = payload.get("html", "")
                target_file = os.path.join(self.output_dir, f"{name}_A4_Report.html")
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                self._send_json({"success": True, "file": target_file})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        # Suppress routine log clutter
        pass


def run_studio_server(port: int = 8089, open_browser: bool = True):
    """Run the A4 Export Studio server."""
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    server = socketserver.ThreadingTCPServer(("", port), StudioRequestHandler)
    server.allow_reuse_address = True
    url = f"http://localhost:{port}/"
    print("\n" + "=" * 55)
    print("JYOTISH A4 EXPORT STUDIO IS RUNNING")
    print(f"Studio URL: {url}")
    print("Modify parameters, toggle pages, edit CSS live, & print A4 PDF")
    print("=" * 55 + "\n")
    sys.stdout.flush()

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Jyotish A4 Studio Server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start Jyotish A4 Export Studio")
    parser.add_argument("--port", type=int, default=8089, help="Server port (default: 8089)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()

    run_studio_server(port=args.port, open_browser=not args.no_browser)
