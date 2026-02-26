import os
import re
import json
import subprocess
import tempfile
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

try:
    subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], capture_output=True, timeout=60)
except Exception:
    pass

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YieldTube — YouTube Downloader</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --cream: #F5F0E8;
    --black: #0D0D0D;
    --charcoal: #1A1A1A;
    --gold: #C9A84C;
    --gold-light: #E8C97A;
    --muted: #888;
    --border: rgba(201,168,76,0.25);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--black);
    color: var(--cream);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Ambient background */
  body::before {
    content: '';
    position: fixed;
    top: -40%;
    left: 50%;
    transform: translateX(-50%);
    width: 900px;
    height: 700px;
    background: radial-gradient(ellipse, rgba(201,168,76,0.08) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  /* Grain texture */
  body::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 1;
    opacity: 0.5;
  }

  .wrapper {
    position: relative;
    z-index: 2;
  }

  /* NAV */
  nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 28px 60px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }

  .logo {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--cream);
  }

  .logo span {
    color: var(--gold);
  }

  nav ul {
    list-style: none;
    display: flex;
    gap: 40px;
  }

  nav ul a {
    text-decoration: none;
    color: var(--muted);
    font-size: 0.85rem;
    font-weight: 400;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    transition: color 0.3s;
  }

  nav ul a:hover { color: var(--cream); }

  .nav-badge {
    background: var(--gold);
    color: var(--black);
    font-size: 0.7rem;
    font-weight: 500;
    padding: 6px 16px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  /* HERO */
  .hero {
    padding: 100px 60px 80px;
    text-align: center;
    max-width: 900px;
    margin: 0 auto;
  }

  .hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 32px;
    opacity: 0;
    animation: fadeUp 0.8s forwards 0.2s;
  }

  .hero-tag::before, .hero-tag::after {
    content: '';
    display: block;
    width: 30px;
    height: 1px;
    background: var(--gold);
  }

  h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3rem, 6vw, 5.5rem);
    font-weight: 700;
    line-height: 1.08;
    letter-spacing: -0.02em;
    margin-bottom: 24px;
    opacity: 0;
    animation: fadeUp 0.8s forwards 0.4s;
  }

  h1 em {
    font-style: italic;
    color: var(--gold);
  }

  .hero p {
    font-size: 1.1rem;
    font-weight: 300;
    color: var(--muted);
    line-height: 1.7;
    max-width: 560px;
    margin: 0 auto 60px;
    opacity: 0;
    animation: fadeUp 0.8s forwards 0.6s;
  }

  /* INPUT CARD */
  .input-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    padding: 10px 10px 10px 28px;
    display: flex;
    align-items: center;
    gap: 12px;
    max-width: 720px;
    margin: 0 auto;
    opacity: 0;
    animation: fadeUp 0.8s forwards 0.8s;
    transition: border-color 0.3s;
  }

  .input-card:focus-within {
    border-color: rgba(201,168,76,0.5);
  }

  .input-icon {
    color: var(--gold);
    flex-shrink: 0;
  }

  .input-card input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: var(--cream);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    font-weight: 300;
  }

  .input-card input::placeholder {
    color: rgba(255,255,255,0.25);
  }

  .btn-fetch {
    background: var(--gold);
    color: var(--black);
    border: none;
    padding: 16px 32px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.3s, transform 0.2s;
    flex-shrink: 0;
  }

  .btn-fetch:hover {
    background: var(--gold-light);
    transform: translateY(-1px);
  }

  .btn-fetch:active { transform: translateY(0); }

  /* FORMATS */
  .formats {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 20px;
    opacity: 0;
    animation: fadeUp 0.8s forwards 1s;
  }

  .format-pill {
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    border: 1px solid rgba(255,255,255,0.1);
    padding: 5px 14px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .format-pill.active, .format-pill:hover {
    border-color: var(--gold);
    color: var(--gold);
  }

  /* RESULT PANEL */
  .result-panel {
    max-width: 720px;
    margin: 40px auto 0;
    display: none;
    opacity: 0;
    animation: fadeUp 0.5s forwards;
  }

  .result-panel.show {
    display: block;
  }

  .video-preview {
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    padding: 24px;
    display: flex;
    gap: 20px;
    align-items: flex-start;
  }

  .video-thumb {
    width: 140px;
    height: 80px;
    object-fit: cover;
    flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.08);
  }

  .video-thumb-placeholder {
    width: 140px;
    height: 80px;
    background: rgba(255,255,255,0.05);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--gold);
  }

  .video-info { flex: 1; }

  .video-title {
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: 8px;
  }

  .video-meta {
    font-size: 0.78rem;
    color: var(--muted);
    display: flex;
    gap: 16px;
  }

  .quality-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: var(--border);
    margin-top: 1px;
  }

  .quality-btn {
    background: var(--charcoal);
    border: none;
    color: var(--cream);
    padding: 16px;
    text-align: center;
    cursor: pointer;
    transition: background 0.2s;
    font-family: 'DM Sans', sans-serif;
  }

  .quality-btn:hover { background: rgba(201,168,76,0.12); }

  .quality-label {
    font-size: 0.95rem;
    font-weight: 500;
    display: block;
    margin-bottom: 4px;
  }

  .quality-sub {
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .download-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    padding: 18px;
    background: var(--gold);
    color: var(--black);
    border: none;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    margin-top: 1px;
    transition: background 0.3s;
  }

  .download-btn:hover { background: var(--gold-light); }

  /* FEATURES */
  .features {
    padding: 100px 60px;
    max-width: 1100px;
    margin: 0 auto;
  }

  .section-label {
    font-size: 0.72rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 60px;
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--border);
  }

  .feature-card {
    background: var(--charcoal);
    padding: 40px 32px;
    transition: background 0.3s;
  }

  .feature-card:hover { background: rgba(201,168,76,0.06); }

  .feature-icon {
    width: 44px;
    height: 44px;
    border: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    color: var(--gold);
  }

  .feature-card h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    font-weight: 600;
    margin-bottom: 12px;
  }

  .feature-card p {
    font-size: 0.85rem;
    color: var(--muted);
    line-height: 1.7;
  }

  /* STATS */
  .stats {
    border-top: 1px solid rgba(255,255,255,0.06);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 60px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    text-align: center;
  }

  .stat {
    border-right: 1px solid rgba(255,255,255,0.06);
    padding: 20px;
  }

  .stat:last-child { border-right: none; }

  .stat-num {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 700;
    color: var(--gold);
    line-height: 1;
    margin-bottom: 8px;
  }

  .stat-label {
    font-size: 0.78rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  /* FOOTER */
  footer {
    padding: 40px 60px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255,255,255,0.06);
  }

  footer p {
    font-size: 0.78rem;
    color: var(--muted);
  }

  footer a {
    color: var(--gold);
    text-decoration: none;
    font-size: 0.78rem;
  }

  /* LOADER */
  .loader {
    display: none;
    text-align: center;
    padding: 40px;
  }

  .loader.show { display: block; }

  .loader-bar {
    width: 200px;
    height: 2px;
    background: rgba(255,255,255,0.1);
    margin: 0 auto 16px;
    overflow: hidden;
    position: relative;
  }

  .loader-bar::after {
    content: '';
    position: absolute;
    left: -100%;
    top: 0;
    width: 100%;
    height: 100%;
    background: var(--gold);
    animation: slide 1.2s infinite;
  }

  .loader p {
    font-size: 0.8rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  /* NOTICE */
  .notice {
    max-width: 720px;
    margin: 20px auto 0;
    padding: 14px 20px;
    background: rgba(201,168,76,0.06);
    border-left: 2px solid var(--gold);
    font-size: 0.78rem;
    color: var(--muted);
    line-height: 1.6;
    opacity: 0;
    animation: fadeUp 0.8s forwards 1.1s;
  }

  .notice a { color: var(--gold); text-decoration: none; }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes slide {
    to { left: 100%; }
  }

  @media (max-width: 768px) {
    nav { padding: 20px 24px; }
    nav ul, .nav-badge { display: none; }
    .hero { padding: 60px 24px; }
    .features { padding: 60px 24px; }
    .features-grid { grid-template-columns: 1fr; }
    .stats { grid-template-columns: repeat(2, 1fr); padding: 40px 24px; }
    footer { flex-direction: column; gap: 12px; padding: 30px 24px; text-align: center; }
    .quality-grid { grid-template-columns: repeat(2, 1fr); }
    .video-preview { flex-direction: column; }
    .video-thumb-placeholder { width: 100%; height: 140px; }
  }
</style>
</head>
<body>
<div class="wrapper">

  <nav>
    <div class="logo">Yield<span>Tube</span></div>
    <ul>
      <li><a href="#">Home</a></li>
      <li><a href="#">Features</a></li>
      <li><a href="#">How It Works</a></li>
      <li><a href="#">FAQ</a></li>
    </ul>
    <div class="nav-badge">Free Tool</div>
  </nav>

  <section class="hero">
    <div class="hero-tag">Professional Downloader</div>
    <h1>Download Any Video,<br><em>Effortlessly.</em></h1>
    <p>The most refined way to save YouTube videos. Choose your quality, pick your format, and download in seconds — no registration required.</p>

    <div class="input-card">
      <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M22.54 6.42a2.78 2.78 0 0 0-1.95-1.96C18.88 4 12 4 12 4s-6.88 0-8.59.46A2.78 2.78 0 0 0 1.46 6.42 29 29 0 0 0 1 12a29 29 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.95 1.96C5.12 20 12 20 12 20s6.88 0 8.59-.46a2.78 2.78 0 0 0 1.95-1.96A29 29 0 0 0 23 12a29 29 0 0 0-.46-5.58z"/>
        <polygon points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02"/>
      </svg>
      <input type="text" id="urlInput" placeholder="Paste YouTube URL here — e.g. https://youtube.com/watch?v=..." />
      <button class="btn-fetch" onclick="fetchVideo()">Fetch Video</button>
    </div>

    <div class="formats">
      <div class="format-pill active" onclick="selectFormat(this, 'mp4')">MP4</div>
      <div class="format-pill" onclick="selectFormat(this, 'mp3')">MP3</div>

    </div>

    <div class="notice">
      ✅ <strong>Live & Functional:</strong> Powered by <a href="https://cobalt.tools" target="_blank">cobalt.tools</a> — paste any YouTube URL and click Fetch, then Download. Works for both MP4 and MP3.
    </div>

    <!-- Loader -->
    <div class="loader" id="loader">
      <div class="loader-bar"></div>
      <p id="loaderText">Fetching video info...</p>
    </div>

    <!-- Result Panel -->
    <div class="result-panel" id="resultPanel">
      <div class="video-preview">
        <div class="video-thumb-placeholder" id="thumbContainer">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </div>
        <div class="video-info">
          <div class="video-title" id="videoTitle">Loading video information...</div>
          <div class="video-meta">
            <span id="videoDuration">—</span>
            <span id="videoChannel">—</span>
          </div>
        </div>
      </div>
      <div class="quality-grid" id="qualityGrid">
        <button class="quality-btn" onclick="selectQuality(this, '4K')">
          <span class="quality-label">4K</span>
          <span class="quality-sub">2160p</span>
        </button>
        <button class="quality-btn selected" onclick="selectQuality(this, '1080p')">
          <span class="quality-label">Full HD</span>
          <span class="quality-sub">1080p</span>
        </button>
        <button class="quality-btn" onclick="selectQuality(this, '720p')">
          <span class="quality-label">HD</span>
          <span class="quality-sub">720p</span>
        </button>
        <button class="quality-btn" onclick="selectQuality(this, '480p')">
          <span class="quality-label">SD</span>
          <span class="quality-sub">480p</span>
        </button>
      </div>
      <button class="download-btn" onclick="startDownload()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Download Video
      </button>
    </div>
  </section>

  <!-- Stats -->
  <div class="stats">
    <div class="stat"><div class="stat-num">4K</div><div class="stat-label">Max Resolution</div></div>
    <div class="stat"><div class="stat-num">2</div><div class="stat-label">Output Formats</div></div>
    <div class="stat"><div class="stat-num">0</div><div class="stat-label">Registration Needed</div></div>
    <div class="stat"><div class="stat-num">∞</div><div class="stat-label">Downloads Free</div></div>
  </div>

  <!-- Features -->
  <section class="features">
    <div class="section-label">Why YieldTube</div>
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
        </div>
        <h3>Lightning Fast</h3>
        <p>Our optimized pipeline ensures your videos are processed and ready for download in seconds, not minutes.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        <h3>Multiple Formats</h3>
        <p>Download as MP4 video or extract MP3 audio. Pristine quality for any device.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <h3>Safe & Private</h3>
        <p>No data stored, no tracking, no registration. Your downloads remain completely private and anonymous.</p>
      </div>
    </div>
  </section>

  <footer>
    <p>© 2026 YieldTube. Built for personal use only.</p>
    <div style="display:flex;gap:24px">
      <a href="#">Terms of Use</a>
      <a href="#">Privacy</a>
      <a href="#">Contact</a>
    </div>
  </footer>

</div>

<script>
  let selectedFormat = 'mp4';
  let selectedQuality = '1080';
  let currentVideoUrl = '';

  const API_BASE = window.location.origin;

  function selectFormat(el, fmt) {
    document.querySelectorAll('.format-pill').forEach(p => p.classList.remove('active'));
    el.classList.add('active');
    selectedFormat = fmt;
    document.getElementById('qualityGrid').style.display = fmt === 'mp3' ? 'none' : 'grid';
  }

  function selectQuality(el, q) {
    document.querySelectorAll('.quality-btn').forEach(b => b.style.background = '');
    el.style.background = 'rgba(201,168,76,0.15)';
    selectedQuality = q;
  }

  function isValidYouTubeUrl(url) {
    return /(?:youtube\\\\.com\\\\/watch|youtu\\\\.be\\\\/|youtube\\\\.com\\\\/shorts\\\\/|youtube\\\\.com\\\\/embed\\\\/)/.test(url);
  }

  function showError(msg) {
    const card = document.querySelector('.input-card');
    const input = document.getElementById('urlInput');
    card.style.borderColor = 'rgba(220,50,50,0.5)';
    input.placeholder = '⚠ ' + msg;
    setTimeout(() => {
      card.style.borderColor = '';
      input.placeholder = 'Paste YouTube URL here — e.g. https://youtube.com/watch?v=...';
    }, 3000);
  }

  async function fetchVideo() {
    const url = document.getElementById('urlInput').value.trim();
    const loader = document.getElementById('loader');
    const panel = document.getElementById('resultPanel');

    if (!url || !isValidYouTubeUrl(url)) {
      showError('Please enter a valid YouTube URL');
      return;
    }

    currentVideoUrl = url;
    panel.classList.remove('show');
    loader.classList.add('show');
    document.getElementById('loaderText').textContent = 'Fetching video info...';

    try {
      const res = await fetch(`${API_BASE}/api/info`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to fetch video info');

      document.getElementById('videoTitle').textContent = data.title;
      document.getElementById('videoChannel').textContent = '\\\\uD83D\\\\uDCFA ' + data.channel;
      document.getElementById('videoDuration').textContent = '\\\\u23F1 ' + data.duration;

      const thumbContainer = document.getElementById('thumbContainer');
      thumbContainer.innerHTML = `<img class="video-thumb" src="${data.thumbnail}" alt="thumbnail" onerror="this.src='https://img.youtube.com/vi/${data.video_id}/mqdefault.jpg'">`;

      const grid = document.getElementById('qualityGrid');
      if (data.formats && data.formats.length > 0) {
        const labels = { 2160: ['4K', '2160p'], 1080: ['Full HD', '1080p'], 720: ['HD', '720p'], 480: ['SD', '480p'] };
        grid.innerHTML = data.formats.map(f => {
          const [name, sub] = labels[f.height] || [f.label, f.label];
          return `<button class="quality-btn" onclick="selectQuality(this, '${f.height}')"><span class="quality-label">${name}</span><span class="quality-sub">${sub}</span></button>`;
        }).join('');
        const firstBtn = grid.querySelector('.quality-btn');
        if (firstBtn) {
          firstBtn.style.background = 'rgba(201,168,76,0.15)';
          selectedQuality = data.formats[0].height;
        }
      }

      loader.classList.remove('show');
      panel.classList.add('show');

    } catch (err) {
      loader.classList.remove('show');
      showError(err.message || 'Failed to fetch video');
    }
  }

  async function startDownload() {
    const btn = document.querySelector('.download-btn');
    if (!currentVideoUrl) return;

    btn.disabled = true;
    btn.innerHTML = `\\\\u23F3 Preparing download...`;

    try {
      const res = await fetch(`${API_BASE}/api/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: currentVideoUrl, quality: selectedQuality, format: selectedFormat })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Download failed');
      }

      if (data.download_url) {
        // Open direct YouTube CDN URL in new tab — browser handles the download
        const a = document.createElement('a');
        a.href = data.download_url;
        a.target = '_blank';
        a.download = data.filename || `video.${selectedFormat}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        btn.innerHTML = `\\\\u2705 Download Started!`;
        btn.style.background = 'rgba(100,200,100,0.15)';
        btn.style.color = '#90ee90';
        setTimeout(resetBtn, 3000);
      } else {
        throw new Error('No download URL received');
      }

    } catch (err) {
      btn.innerHTML = `\\\\u274C ${err.message}`;
      btn.style.background = 'rgba(220,50,50,0.15)';
      btn.style.color = '#f88';
      setTimeout(resetBtn, 4000);
    }
  }

  function resetBtn() {
    const btn = document.querySelector('.download-btn');
    btn.disabled = false;
    btn.style.background = '';
    btn.style.color = '';
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Download ${selectedFormat.toUpperCase()}`;
  }

  document.getElementById('urlInput').addEventListener('keydown', e => { if (e.key === 'Enter') fetchVideo(); });
  document.getElementById('urlInput').addEventListener('paste', () => {
    setTimeout(() => { const v = document.getElementById('urlInput').value.trim(); if (isValidYouTubeUrl(v)) fetchVideo(); }, 100);
  });

  // Keep-alive ping every 14 minutes to prevent Render free tier spin-down
  async function pingServer() {
    try {
      await fetch(`${API_BASE}/api/health`);
    } catch(e) {}
  }
  setInterval(pingServer, 14 * 60 * 1000);

  // On page load, ping immediately and show status
  window.addEventListener('load', async () => {
    const notice = document.querySelector('.notice');
    notice.innerHTML = '🔄 <strong>Waking up server...</strong> This may take up to 30 seconds on first load.';
    try {
      const start = Date.now();
      const res = await fetch(`${API_BASE}/api/health`);
      const elapsed = ((Date.now() - start) / 1000).toFixed(1);
      if (res.ok) {
        notice.innerHTML = `✅ <strong>Server is live</strong> — responded in ${elapsed}s. Powered by <a href="https://cobalt.tools" target="_blank">yt-dlp</a>. Paste a URL above to begin.`;
        notice.style.borderLeftColor = '#4CAF50';
      }
    } catch(e) {
      notice.innerHTML = '⚠️ <strong>Server is starting up</strong> — please wait a moment and try your download.';
    }
  });
</script>
</body>
</html>
"""

def is_valid_youtube_url(url):
    return bool(re.search(r'(?:youtube\\.com/watch|youtu\\.be/|youtube\\.com/shorts/|youtube\\.com/embed/)', url))

@app.route('/')
def index():
    return Response(HTML, mimetype='text/html')

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    try:
        result = subprocess.run(['yt-dlp', '--dump-json', '--no-playlist', url], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return jsonify({'error': 'Could not fetch video info. Video may be private or unavailable.'}), 400
        info = json.loads(result.stdout)
        formats = []
        seen_heights = set()
        for f in info.get('formats', []):
            h = f.get('height')
            ext = f.get('ext')
            vcodec = f.get('vcodec', 'none')
            if h and vcodec != 'none' and h not in seen_heights and ext in ('mp4', 'webm'):
                seen_heights.add(h)
                formats.append({'height': h, 'label': f'{h}p'})
        formats = sorted(formats, key=lambda x: x['height'], reverse=True)
        filtered = []
        for s in [2160, 1080, 720, 480]:
            match = next((f for f in formats if f['height'] == s), None)
            if match:
                filtered.append(match)
        duration_sec = info.get('duration', 0)
        duration_str = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}" if duration_sec else 'N/A'
        return jsonify({'title': info.get('title', 'Unknown Title'), 'channel': info.get('uploader', 'Unknown Channel'), 'duration': duration_str, 'thumbnail': info.get('thumbnail', ''), 'video_id': info.get('id', ''), 'formats': filtered})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Request timed out. Try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url', '').strip()
    quality = data.get('quality', '1080')
    fmt = data.get('format', 'mp4')
    if not url or not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid URL'}), 400
    try:
        height = str(quality).replace('p', '')
        fmt_selector = 'bestaudio[ext=m4a]/bestaudio' if fmt == 'mp3' else f'best[height<={height}][ext=mp4]/best[height<={height}]/best'
        result = subprocess.run(['yt-dlp', '-f', fmt_selector, '--get-url', '--no-playlist', url], capture_output=True, text=True, timeout=25)
        if result.returncode != 0 or not result.stdout.strip():
            result = subprocess.run(['yt-dlp', '-f', 'best', '--get-url', '--no-playlist', url], capture_output=True, text=True, timeout=25)
        if result.returncode != 0 or not result.stdout.strip():
            return jsonify({'error': 'Could not get download URL. Try a different quality.'}), 500
        direct_url = result.stdout.strip().split('\n')[0]
        return jsonify({'download_url': direct_url, 'filename': f'video.{"mp3" if fmt == "mp3" else "mp4"}'})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timed out. Try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
