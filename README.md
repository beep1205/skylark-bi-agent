# skylark-bi-agent
# Skylark Drones — BI Agent

AI-powered Business Intelligence agent for monday.com boards.

## Setup
1. Install dependencies: `pip install flask anthropic requests`
2. Set your API keys in main.py
3. Run: `python main.py`

## Architecture
- Backend: Flask + Anthropic Claude API
- Data Source: monday.com REST API (Work Orders + Deals boards)
- Hosting: Cloudflare Tunnel

## Live Demo
https://forest-seller-rip-existence.trycloudflare.com
