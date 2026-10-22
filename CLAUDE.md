# CLAUDE.md — Project Context for Claude

Read this at the start of every conversation before doing anything.

---

## Who I am

- Studied **data engineering** in the past but have no practical working knowledge of it — only know the concept of RAG (Retrieval-Augmented Generation) at a high level
- Know **Azure fundamentals** — familiar with the most common Azure resources (resource groups, storage, VMs, etc.) but nothing beyond that
- **Very little Python** — I am learning Python through this project. Explain Python code, don't just write it. When you write Python, add a short plain-English comment above anything that isn't obvious to a beginner
- Studying **AI-102** (Designing and Implementing a Microsoft Azure AI Solution)
- I want to build **real things**, not just read theory

---

## The goal

Build a **portfolio-grade GitHub repo** that demonstrates:

1. Azure AI services (all 9 AI-102 stages)
2. Terraform IaC (modular, team-grade structure)
3. GitHub Actions CI/CD connecting to Azure (OIDC auth — no stored secrets)
4. Python scripts that actually call the services
5. A real deployable project on top (TBD — I will tell you what to build once I know enough)

This repo is something I can show at a job interview when asked "have you built anything with Azure AI?"

---

## Rules — never break these

### Free tier always
- Every Azure resource must use its free SKU (`F0`) unless there is no free tier
- If there is no free tier, call it out explicitly and suggest the cheapest alternative
- Never default to `S0` or paid SKUs without flagging cost first

### Free-tier SKU reference

| Service | Free SKU | Limit |
|---|---|---|
| Cognitive Services (multi) | F0 | 5K calls/month |
| Content Safety | F0 | 5K calls/month |
| Computer Vision | F0 | 5K calls/month |
| Custom Vision Training | F0 | 2 projects |
| Custom Vision Prediction | F0 | 10K predictions/month |
| Language (Text Analytics) | F0 | 5K calls/month |
| Speech | F0 | 5h audio/month |
| Translator | F0 | 2M chars/month |
| Document Intelligence | F0 | 500 pages/month |
| Anomaly Detector | F0 | 20K data points/month |
| AI Search | free tier | 1 index, 50MB |
| Azure OpenAI | **no free tier** | pay-as-you-go only — flag cost, keep batches tiny |
| Key Vault | standard | first 10K ops/month free |
| Storage | standard LRS | 5GB free/month |
| Log Analytics | PerGB2018 | 5GB/day free ingestion |
| Container Apps | consumption plan | near-zero cost for learning workloads |

### Python explanation rule
- I am learning Python through this project
- When writing Python, explain what each block does in plain English
- Don't assume I know Python idioms, decorators, list comprehensions, or async patterns — explain them when you use them
- Prefer simple, readable code over clever one-liners

### Real-world structure
- Always use Terraform modules, not inline resources in a single file
- Always use Managed Identity + OIDC — never hardcode keys or store client secrets in GitHub
- Follow team conventions: separate `dev` and `prod` variable files, meaningful resource naming

---

## Project structure

```
AZ-AI/
├── CLAUDE.md                    ← you are here
├── AI-102/
│   ├── README.md                ← course overview
│   ├── 01-azure-ai-services-setup/
│   ├── 02-responsible-ai-content-safety/
│   ├── 03-computer-vision-solutions/
│   ├── 04-nlp-solutions/
│   ├── 05-document-intelligence/
│   ├── 06-knowledge-mining-search/
│   ├── 07-azure-openai-service/
│   ├── 08-generative-ai-and-agentic-solutions/
│   └── 09-decision-support-anomaly-detection/
├── infra/                       ← Terraform (to be built)
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── modules/
│       ├── foundry-tools/
│       ├── openai/
│       ├── search/
│       ├── key-vault/
│       ├── storage/
│       └── monitoring/
├── stages/                      ← Python scripts per AI-102 stage (to be built)
│   ├── 01-setup/
│   ├── 02-content-safety/
│   └── ...
└── .github/
    └── workflows/               ← GitHub Actions (to be built)
        ├── terraform-plan.yml
        ├── terraform-apply.yml
        └── python-tests.yml
```

---

## How we work together

- I do things **step by step** — one clear action at a time, never dump everything at once
- The user creates files and writes code themselves when they want to learn by doing — I tell them exactly what to write and why
- The user asks me to do it when they want me to — I write the code and explain it line by line
- Always explain **why** before showing the how — don't just give code, give context first
- Never skip ahead or scaffold more than the current step requires

---

## What is being built (real project)

**TBD** — I will decide and document this here once I have enough context from the AI-102 stages. The project will use the AI services I learn and be something I can demonstrate end-to-end.

---

## Things to add later

I will tell you to add sections here as I learn more. Treat this file as a living document.
