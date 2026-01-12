---
name: 'workflow-init'
description: 'Initialize BMAD workflow for your project'
---

# BMAD Workflow Initialization

Help the user choose the right development track for their project.

## Available Tracks

Present these options to the user:

### 1. Quick Flow (Bug fixes, small features)
- Best for: Single feature, bug fix, small enhancement
- Time to first story: ~5 minutes
- Commands: `/bmad:bmm:workflows:quick-spec` then `/bmad:bmm:workflows:quick-dev`

### 2. BMad Method (Products and platforms)
- Best for: New products, major features, platform development
- Time to first story: ~15 minutes
- Flow: Analysis → Planning → Solutioning → Implementation
- Start with: `/bmad:bmm:agents:pm` or `/bmad:bmm:workflows:product-brief`

### 3. Brainstorming (Explore ideas)
- Best for: Idea exploration, problem solving
- Commands: `/bmad:core:workflows:brainstorming`

## Ask the User

1. What type of project are you starting?
2. Do you have an existing idea or starting from scratch?
3. What's the scope? (bug fix, feature, product, platform)

Based on their answers, recommend the appropriate track and guide them to the first step.

## Available Agents

- **PM (John)** - Product Manager for PRDs and requirements
- **Architect (Archie)** - Technical architecture and design
- **Dev** - Development implementation
- **SM** - Scrum Master for sprint management
- **UX Designer** - User experience design
- **Analyst** - Business and market analysis
- **Quick Flow Solo Dev** - For small tasks end-to-end

Launch agents with: `/bmad:{module}:agents:{agent-name}`
