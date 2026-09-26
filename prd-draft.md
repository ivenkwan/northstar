# Project North Star
Enterprise Sales Assistant — AI Agent Mobile App
A mobile-first enterprise sales assistant where each salesperson gets a personal AI agent that answers questions about their pipeline, quota, and market — and renders answers as live charts, tables, and news cards. The app is organized around a four-tab shell (Dashboard, Assistant, Intelligence, Settings), a self-configurable dashboard that persists per user, and a conversational chat that turns natural-language questions into visual data. The data model captures the full hierarchy (salesperson to team to domain to groups) with secure per-role access, and an AI backend function bridges the chat to the database.

## 1. Product Proposal & Vision

Define the product as a conversational AI sales assistant mobile app for enterprise sales teams
Each salesperson gets a personal AI agent that understands their pipeline, targets, and market context
The agent answers questions in natural language and renders answers as interactive charts, graphs, and tables
Users can self-configure their dashboard layout — choosing which widgets (pipeline funnel, quota tracker, market news feed, company intel card) appear and in what arrangement
The app serves three hierarchy levels: individual salesperson, team roll-up, and domain roll-up, with groups sitting above domains
Value proposition: salespeople spend less time digging through CRM tabs and more time selling, because the assistant proactively surfaces deal risks, quota gaps, and market signals in one place

## 2. Organizational Hierarchy & Data Model

Define the hierarchy: Salesperson belongs to a Team; multiple Teams belong to a Domain; a Domain can belong to multiple Groups (many-to-many between domains and groups)
Design database tables to store this hierarchy:
Groups, Domains, and a join table linking domains to groups (since a domain can belong to multiple groups)
Teams linked to a domain
Salespeople linked to a team, with user accounts tied to authentication
Design sales-data tables:
Deals/opportunities (stage, value, expected close date, probability) owned by a salesperson
Quota targets per salesperson per period (quarterly/monthly) with actuals tracked against plan
Market intelligence entries tagged by industry, company, or domain (news articles, competitor moves, analyst notes)
Design an AI conversation history table so each salesperson's chat threads and messages persist across sessions
Design a dashboard configuration table so each user's self-configured widget layout is saved and restored on reopen
Apply row-level security so salespeople only see their own deals and conversations, while managers can see team/domain roll-ups

## 3. Authentication & Onboarding

Add email/password sign-in and sign-up screens using Bolt Database authentication
Add a role field during onboarding (salesperson, team manager, domain manager) that determines what data is visible
Show a brief in-app onboarding flow on first launch: explain the assistant, connect to their team, and pick initial dashboard widgets
Keep users signed in between visits with persistent sessions
Route unauthenticated users to a login screen and authenticated users to the main app

## 4. Conversational AI Agent Interface

Build a chat screen as the primary interaction surface — a message thread where the salesperson types or speaks questions
The agent interprets each question and decides what to return: a chart, a table, a number, a news summary, or a text answer
Support example prompt chips above the input bar ("How is my pipeline looking this quarter?", "What's my quota gap?", "Any news on Acme Corp?", "Show me deals at risk")
The agent can pull from: the salesperson's deals, quota vs actuals, team roll-up, and market intelligence tagged by company/industry/domain
Render agent responses inline as rich content blocks: bar/line/donut charts, data tables, KPI cards, and news list items — not just plain text
Persist conversation history so the user can scroll back through past threads

## 5. Self-Configurable Dashboard

Build a dashboard screen that the user lands on after login, showing their selected widgets in a scrollable, rearrangeable layout
Default widgets: Pipeline Funnel, Quota vs Plan tracker, Deals at Risk, Market Intelligence feed, Team Leaderboard
Let users add, remove, and reorder widgets through an edit mode (drag to reorder, tap to remove, add from a widget library)
Save each user's layout to the database so it persists across sessions and devices
Each widget is tappable to expand into a full-screen detail view or to ask the AI agent a follow-up question about that data

## 6. Market Intelligence Module

Build a market intelligence feed that surfaces news and insights tagged by industry, company, or domain
Allow the salesperson to follow specific companies and industries so the feed personalizes to their territory
Each intelligence card shows a headline, source, date, relevance tag (company/industry/domain), and a one-tap action to ask the AI agent "What does this mean for my deals?"
Support a search and filter bar to narrow the feed by company, industry, or domain
Store followed topics per user so the feed stays relevant

## 7. Navigation & App Shell

Set up a bottom tab navigation with four tabs: Dashboard, Assistant (chat), Intelligence, and Profile/Settings
Dashboard tab shows the self-configurable widget layout
Assistant tab opens the conversational AI chat
Intelligence tab shows the market intelligence feed and followed topics
Profile/Settings tab shows user info, role, team assignment, and dashboard reset options
Ensure the app works as a mobile-first layout with proper safe-area handling and responsive sizing

## 8. AI Agent Backend & Data Pipeline

Set up function that receives a salesperson's question, gathers relevant data (deals, quota, team, intelligence), and returns a structured response the app can render as charts/tables/text
The function reads the user's deals, quota progress, and relevant market intelligence from the database, then asks a language model to summarize or answer
The function returns a typed payload (e.g., "render a bar chart of pipeline by stage" or "render a table of deals at risk") so the app knows which visual component to draw
Include a fallback so if the AI cannot structure a visual, it returns a plain-text answer
Keep all database access server-side so the salesperson only sees data their role permits