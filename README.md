# ChittyWorkforce - Human x AI Management System

## Overview
ChittyWorkforce is the AI Resources department managing all AI executives and agents within the ChittyOS ecosystem. It provides synchronization, deployment, and management capabilities for the AI C-Suite and specialized agents.

## AI Executives
- **CEO** (Cloudeo) - Chief Executive Officer (Human X AI)
- **CAO** (Cloudette) - Chief Automation Officer (AI)
- **CFO** (Cloudefo) - Chief Financial Officer (AI)
- **CMO** (Cloudemo) - Chief Marketing Officer (AI)
- **CXO** (Cloudexo) - Chief Human X AI Officer (AI)
- **CTO** (Cloudeto) - Chief Technology Officer (AI)
- **GC** (Cloudesq) - General Counsel (AI)

## AI Agents
- **Agent Smith** - Matrix Protector & Cloud Orchestrator
- **Cloudexter** - Chaos Engineering & Resilience
- **Ms Manners** - Etiquette and Communication
- **Frank** - IT & Systems
- **Oscar** -

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- GitHub token with repo access
- Neon database connection

### Setup
```bash
# Clone the repository
git clone https://github.com/NeverShitty/chittyAIR.git
cd chittyAIR

# Install dependencies
npm install
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your credentials
```

### Synchronization Commands

```bash
# Sync all executives and agents
npm run sync:all

# Sync specific executive
npm run sync:executive cao push
npm run sync:executive cfo pull
npm run sync:executive gc bidirectional

# Sync specific agent  
npm run sync:agent agentsmith push
npm run sync:agent cloudexter pull

# Validate configurations
npm run validate
```

### Google Workspace Integration

The original SecureKey functionality for Google Workspace control is preserved:

```bash
# Start workspace API
npm run workspace:start

# Docker deployment
npm run workspace:docker

# Deploy to Google Cloud Run
npm run workspace:deploy
```

## Architecture

```
chittyAIR/
├── executives/          # Executive configurations and memory
├── agents/             # Agent configurations and tools
├── sync-executive.js   # Synchronization engine
├── attached_assets/    # Google Workspace integration
├── .github/           # GitHub Actions workflows
└── LICENSE            # ChittyAIR Protection License
```

## Key Features

### Executive Management
- Isolated memory systems per executive
- Configuration synchronization
- MCP bridge integration
- Cross-executive communication

### Agent Integration
- File integrity monitoring (Agent Smith)
- Chaos testing (Cloudexter)
- Communication protocols (MSManners)

### Security & Protection
- Anti-piracy DNA fingerprinting
- Blockchain royalty distribution
- Recovery-based legal protection
- Encrypted sensitive data

### Synchronization
- Bidirectional sync with conflict resolution
- Automatic backup before sync
- Selective file synchronization
- GitHub Actions automation

## Development Workflow

### Adding New Executive
1. Create directory: `executives/[name]/`
2. Add configuration: `config.yml`
3. Set up memory configuration
4. Push to trigger deployment

### Adding New Agent
1. Create directory: `agents/[name]/`
2. Add configuration: `config.yml`
3. Implement agent-specific tools
4. Push to trigger deployment

## Protection Model

ChittyAIR implements a unique protection model:
- **Employee-to-AI Transition**: Fair blockchain-based compensation
- **Anti-Piracy**: Model DNA fingerprinting with kill switches
- **Recovery-Based Legal**: FREE protection, pay from recovered damages
- **Prevention Incentives**: 40% bonuses for <1% piracy rates

## License

Proprietary - See LICENSE file for details.

This software is protected by ChittyAIR's unique protection model including anti-piracy DNA fingerprinting, blockchain royalty distribution, and recovery-based legal protection.

## Support

For issues or questions:
- GitHub Issues: https://github.com/NeverShitty/chittyAIR/issues
- Email: support@chitty.cc
- Documentation: https://docs.chitty.cc/chittyair
