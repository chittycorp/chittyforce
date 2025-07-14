#!/usr/bin/env node

import { Octokit } from '@octokit/rest';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class ChittyAirDiscoverySync {
  constructor() {
    this.github = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });
    this.owner = process.env.GITHUB_OWNER || 'NeverShitty';
    this.repo = process.env.GITHUB_REPO || 'chittyAIR';
    
    // Auto-discover ChittyAIR paths
    this.chittyRoot = this.findChittyRoot();
    this.execPath = path.join(this.chittyRoot, 'ai', 'exec');
    this.agentsPath = path.join(this.chittyRoot, 'ai', 'agents');
  }

  findChittyRoot() {
    // Look for MAIN directory structure
    const possiblePaths = [
      process.env.CHITTYAIR_ROOT,
      '/Users/' + os.userInfo().username + '/MAIN',
      process.cwd(),
      path.join(os.homedir(), 'MAIN'),
    ].filter(Boolean);

    for (const rootPath of possiblePaths) {
      const aiPath = path.join(rootPath, 'ai');
      if (fs.existsSync(aiPath)) {
        console.log(`🎯 Found ChittyAIR root: ${rootPath}`);
        return rootPath;
      }
    }
    
    throw new Error('ChittyAIR root directory not found. Set CHITTYAIR_ROOT environment variable.');
  }

  async discoverExecutives() {
    const executives = [];
    
    if (!fs.existsSync(this.execPath)) {
      console.log('⚠️ No executives directory found');
      return executives;
    }

    const dirs = await fs.readdir(this.execPath);
    
    for (const dir of dirs) {
      const execDir = path.join(this.execPath, dir);
      const stat = await fs.stat(execDir);
      
      if (stat.isDirectory()) {
        const executive = await this.analyzeExecutive(dir, execDir);
        if (executive) {
          executives.push(executive);
        }
      }
    }
    
    return executives;
  }

  async analyzeExecutive(name, execDir) {
    console.log(`🔍 Analyzing executive: ${name}`);
    
    const executive = {
      name: name.toUpperCase(),
      localName: name,
      type: 'executive',
      path: execDir,
      discovered: new Date().toISOString(),
    };

    // Check for existing profile
    const profilePaths = [
      path.join(execDir, 'id', `${name}_profile.json`),
      path.join(execDir, 'id', 'profile.json'),
      path.join(execDir, `${name}_profile.json`),
    ];

    for (const profilePath of profilePaths) {
      if (await fs.pathExists(profilePath)) {
        try {
          executive.profile = await fs.readJson(profilePath);
          console.log(`  ✅ Found profile: ${profilePath}`);
          break;
        } catch (error) {
          console.log(`  ⚠️ Invalid profile JSON: ${profilePath}`);
        }
      }
    }

    // Discover services
    executive.services = await this.discoverServices(execDir);

    // Check for MCP bridge
    const mcpBridgePath = path.join(execDir, 'mcp-bridge');
    if (await fs.pathExists(mcpBridgePath)) {
      executive.mcpBridge = {
        enabled: true,
        path: mcpBridgePath,
      };
      
      // Check for package.json to get MCP servers
      const packagePath = path.join(mcpBridgePath, 'package.json');
      if (await fs.pathExists(packagePath)) {
        try {
          const packageJson = await fs.readJson(packagePath);
          executive.mcpBridge.dependencies = packageJson.dependencies;
        } catch (error) {
          console.log(`  ⚠️ Could not read MCP bridge package.json`);
        }
      }
    }

    // Check for memory configuration
    const memoryConfigPath = path.join(execDir, 'id', 'memory_config.json');
    if (await fs.pathExists(memoryConfigPath)) {
      try {
        executive.memoryConfig = await fs.readJson(memoryConfigPath);
        console.log(`  ✅ Found memory config`);
      } catch (error) {
        console.log(`  ⚠️ Invalid memory config JSON`);
      }
    }

    // Discover directory structure
    executive.structure = await this.analyzeDirectoryStructure(execDir);

    return executive;
  }

  async discoverServices(execDir) {
    const services = {};
    const sysPath = path.join(execDir, 'sys');
    
    if (!await fs.pathExists(sysPath)) {
      return services;
    }

    const files = await fs.readdir(sysPath);
    
    for (const file of files) {
      const filePath = path.join(sysPath, file);
      const stat = await fs.stat(filePath);
      
      if (file.endsWith('.js') && file.includes('service')) {
        const serviceName = file.replace('.js', '');
        services[serviceName] = {
          type: 'javascript',
          path: path.relative(execDir, filePath),
          discovered: true,
        };
      } else if (stat.isDirectory()) {
        // Check if directory contains a service
        const dirFiles = await fs.readdir(filePath);
        if (dirFiles.includes('index.js') || dirFiles.includes('package.json')) {
          services[file] = {
            type: 'module',
            path: path.relative(execDir, filePath),
            discovered: true,
          };
        }
      }
    }
    
    return services;
  }

  async analyzeDirectoryStructure(execDir) {
    const structure = {};
    
    const standardDirs = ['sys', 'dev', 'temp', 'id', 'mcp-bridge'];
    
    for (const dir of standardDirs) {
      const dirPath = path.join(execDir, dir);
      if (await fs.pathExists(dirPath)) {
        const stat = await fs.stat(dirPath);
        structure[dir] = {
          exists: true,
          path: dirPath,
          modified: stat.mtime,
        };
      }
    }
    
    return structure;
  }

  async discoverAgents() {
    const agents = [];
    
    if (!fs.existsSync(this.agentsPath)) {
      console.log('⚠️ No agents directory found');
      return agents;
    }

    const dirs = await fs.readdir(this.agentsPath);
    
    for (const dir of dirs) {
      const agentDir = path.join(this.agentsPath, dir);
      const stat = await fs.stat(agentDir);
      
      if (stat.isDirectory()) {
        const agent = await this.analyzeAgent(dir, agentDir);
        if (agent) {
          agents.push(agent);
        }
      }
    }
    
    return agents;
  }

  async analyzeAgent(name, agentDir) {
    console.log(`🔍 Analyzing agent: ${name}`);
    
    const agent = {
      name,
      type: 'agent',
      path: agentDir,
      discovered: new Date().toISOString(),
    };

    // Look for README to understand purpose
    const readmePath = path.join(agentDir, 'README.md');
    if (await fs.pathExists(readmePath)) {
      const readme = await fs.readFile(readmePath, 'utf8');
      agent.description = readme.split('\n')[0].replace('#', '').trim();
    }

    // Discover tools and scripts
    agent.tools = await this.discoverAgentTools(agentDir);
    
    // Check for configuration files
    const configFiles = ['package.json', 'config.json', `${name}.json`];
    for (const configFile of configFiles) {
      const configPath = path.join(agentDir, configFile);
      if (await fs.pathExists(configPath)) {
        try {
          agent.config = await fs.readJson(configPath);
          console.log(`  ✅ Found config: ${configFile}`);
          break;
        } catch (error) {
          console.log(`  ⚠️ Invalid config JSON: ${configFile}`);
        }
      }
    }

    return agent;
  }

  async discoverAgentTools(agentDir) {
    const tools = [];
    
    const files = await fs.readdir(agentDir);
    
    for (const file of files) {
      const filePath = path.join(agentDir, file);
      const stat = await fs.stat(filePath);
      
      if (stat.isFile() && (file.endsWith('.js') || file.endsWith('.py'))) {
        tools.push({
          name: file,
          type: path.extname(file).substring(1),
          path: filePath,
          size: stat.size,
          modified: stat.mtime,
        });
      }
    }
    
    return tools;
  }

  async generateSyncManifest() {
    console.log('🚀 Discovering ChittyAIR infrastructure...\n');
    
    const manifest = {
      generated: new Date().toISOString(),
      chittyRoot: this.chittyRoot,
      paths: {
        executives: this.execPath,
        agents: this.agentsPath,
      },
      discovery: {
        executives: await this.discoverExecutives(),
        agents: await this.discoverAgents(),
      },
      sync: {
        strategy: 'discovery-based',
        conflicts: 'auto-resolve',
        backup: 'before-sync',
      },
    };

    console.log(`\n📊 Discovery Summary:`);
    console.log(`  Executives: ${manifest.discovery.executives.length}`);
    console.log(`  Agents: ${manifest.discovery.agents.length}`);
    
    return manifest;
  }

  async syncToGitHub() {
    const manifest = await this.generateSyncManifest();
    
    // Upload manifest
    await this.updateGitHubFile(
      'discovery-manifest.json',
      JSON.stringify(manifest, null, 2),
      'Update ChittyAIR discovery manifest'
    );

    // Sync each executive
    for (const executive of manifest.discovery.executives) {
      await this.syncExecutiveToGitHub(executive);
    }

    // Sync each agent
    for (const agent of manifest.discovery.agents) {
      await this.syncAgentToGitHub(agent);
    }

    console.log('\n✅ Sync to GitHub completed!');
  }

  async syncExecutiveToGitHub(executive) {
    const remotePath = `executives/${executive.localName}`;
    
    // Generate dynamic config based on discovery
    const config = {
      ...executive,
      lastSync: new Date().toISOString(),
      source: 'auto-discovered',
    };

    await this.updateGitHubFile(
      `${remotePath}/auto-config.json`,
      JSON.stringify(config, null, 2),
      `Auto-sync ${executive.name} configuration`
    );

    console.log(`✅ Synced executive: ${executive.name}`);
  }

  async syncAgentToGitHub(agent) {
    const remotePath = `agents/${agent.name}`;
    
    // Generate dynamic config based on discovery
    const config = {
      ...agent,
      lastSync: new Date().toISOString(),
      source: 'auto-discovered',
    };

    await this.updateGitHubFile(
      `${remotePath}/auto-config.json`,
      JSON.stringify(config, null, 2),
      `Auto-sync ${agent.name} configuration`
    );

    console.log(`✅ Synced agent: ${agent.name}`);
  }

  async updateGitHubFile(filePath, content, message) {
    try {
      let sha;
      try {
        const { data } = await this.github.repos.getContent({
          owner: this.owner,
          repo: this.repo,
          path: filePath,
        });
        sha = data.sha;
      } catch (error) {
        // File doesn't exist, will create new
      }

      await this.github.repos.createOrUpdateFileContents({
        owner: this.owner,
        repo: this.repo,
        path: filePath,
        message,
        content: Buffer.from(content).toString('base64'),
        sha,
      });

    } catch (error) {
      console.error(`❌ Failed to update ${filePath}:`, error.message);
    }
  }
}

// CLI handling
if (import.meta.url === `file://${process.argv[1]}`) {
  const action = process.argv[2] || 'discover';
  
  const sync = new ChittyAirDiscoverySync();
  
  try {
    switch (action) {
      case 'discover':
        const manifest = await sync.generateSyncManifest();
        console.log('\n📄 Generated manifest:');
        console.log(JSON.stringify(manifest, null, 2));
        break;
        
      case 'sync':
        await sync.syncToGitHub();
        break;
        
      default:
        console.log(`
Usage: node discover-and-sync.js [action]

Actions:
  discover  - Discover and analyze ChittyAIR infrastructure (default)
  sync      - Discover and sync to GitHub

Environment variables:
  GITHUB_TOKEN     - GitHub API token
  CHITTYAIR_ROOT   - Root path to ChittyAIR (auto-detected if not set)
        `);
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

export default ChittyAirDiscoverySync;