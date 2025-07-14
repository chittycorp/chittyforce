#!/usr/bin/env node

import { Octokit } from '@octokit/rest';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import yaml from 'yaml';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class ExecutiveSync {
  constructor() {
    this.github = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });
    this.owner = 'NeverShitty';
    this.repo = 'chittyAIR';
    this.localBasePath = '/Users/nickbianchi/MAIN/ai/exec';
    this.agentsPath = '/Users/nickbianchi/MAIN/ai/agents';
    this.executives = ['cao', 'cfo', 'cio', 'cmo', 'coo', 'ceo', 'cto', 'gc'];
    this.agents = ['agentsmith', 'cloudexter', 'msmanners'];
  }

  async syncExecutive(executive, direction = 'bidirectional') {
    console.log(`🔄 Syncing executive: ${executive.toUpperCase()}`);
    
    const localPath = path.join(this.localBasePath, executive);
    const remotePath = `executives/${executive}`;

    if (direction === 'push' || direction === 'bidirectional') {
      await this.pushExecutive(executive, localPath, remotePath);
    }

    if (direction === 'pull' || direction === 'bidirectional') {
      await this.pullExecutive(executive, localPath, remotePath);
    }
  }

  async syncAgent(agent, direction = 'bidirectional') {
    console.log(`🔄 Syncing agent: ${agent}`);
    
    const localPath = path.join(this.agentsPath, agent);
    const remotePath = `agents/${agent}`;

    if (direction === 'push' || direction === 'bidirectional') {
      await this.pushAgent(agent, localPath, remotePath);
    }

    if (direction === 'pull' || direction === 'bidirectional') {
      await this.pullAgent(agent, localPath, remotePath);
    }
  }

  async pushExecutive(executive, localPath, remotePath) {
    console.log(`⬆️  Pushing ${executive} to GitHub...`);

    const config = await this.generateExecutiveConfig(executive, localPath);
    
    await this.updateGitHubFile(
      `${remotePath}/config.yml`,
      yaml.stringify(config),
      `Update ${executive} configuration`
    );

    const systemFiles = await this.getSystemFiles(localPath);
    for (const file of systemFiles) {
      const content = await fs.readFile(file.path, 'utf8');
      const relativePath = file.path.replace(localPath, '').substring(1);
      await this.updateGitHubFile(
        `${remotePath}/sys/${relativePath}`,
        content,
        `Update ${executive} system file: ${relativePath}`
      );
    }

    const memorySnapshot = await this.exportMemorySnapshot(executive);
    if (memorySnapshot) {
      await this.updateGitHubFile(
        `${remotePath}/memory/snapshot.json`,
        JSON.stringify(memorySnapshot, null, 2),
        `Update ${executive} memory snapshot`
      );
    }
  }

  async generateExecutiveConfig(executive, localPath) {
    const config = {
      name: executive.toUpperCase(),
      type: 'executive',
      version: '1.0.0',
      lastSync: new Date().toISOString(),
      paths: {
        local: localPath,
        sys: path.join(localPath, 'sys'),
        dev: path.join(localPath, 'dev'),
        temp: path.join(localPath, 'temp')
      },
      services: {},
      memory: {
        enabled: true,
        version: 'v5',
        isolation: true
      },
      mcp: {
        enabled: true,
        bridge: path.join(localPath, 'mcp-bridge')
      }
    };

    // Read executive profile if exists
    const profilePath = path.join(localPath, 'id', `${executive}_profile.json`);
    if (await fs.pathExists(profilePath)) {
      config.profile = await fs.readJson(profilePath);
    }

    return config;
  }

  async getSystemFiles(localPath) {
    const files = [];
    const sysPath = path.join(localPath, 'sys');
    
    if (await fs.pathExists(sysPath)) {
      const walk = async (dir) => {
        const items = await fs.readdir(dir);
        for (const item of items) {
          const fullPath = path.join(dir, item);
          const stat = await fs.stat(fullPath);
          
          if (stat.isDirectory()) {
            await walk(fullPath);
          } else if (this.shouldSyncFile(item)) {
            files.push({
              path: fullPath,
              name: item,
              relativePath: path.relative(sysPath, fullPath)
            });
          }
        }
      };
      
      await walk(sysPath);
    }
    
    return files;
  }

  shouldSyncFile(filename) {
    const syncExtensions = ['.js', '.yml', '.yaml', '.json', '.md'];
    const excludePatterns = [
      'node_modules',
      '.env',
      'secrets',
      'private',
      '.log',
      'temp'
    ];

    const ext = path.extname(filename);
    const shouldSync = syncExtensions.includes(ext);
    const shouldExclude = excludePatterns.some(pattern => 
      filename.includes(pattern)
    );

    return shouldSync && !shouldExclude;
  }

  async exportMemorySnapshot(executive) {
    return {
      executive,
      exportedAt: new Date().toISOString(),
      publicMemories: [],
      stats: {
        totalMemories: 0,
        publicMemories: 0,
        lastActivity: new Date().toISOString()
      }
    };
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

      console.log(`✅ Updated: ${filePath}`);
    } catch (error) {
      console.error(`❌ Failed to update ${filePath}:`, error.message);
    }
  }

  async syncAll() {
    console.log('🚀 Starting full sync...');
    
    for (const executive of this.executives) {
      const localPath = path.join(this.localBasePath, executive);
      if (await fs.pathExists(localPath)) {
        await this.syncExecutive(executive);
      }
    }
    
    for (const agent of this.agents) {
      const localPath = path.join(this.agentsPath, agent);
      if (await fs.pathExists(localPath)) {
        await this.syncAgent(agent);
      }
    }
    
    console.log('✅ Full sync completed!');
  }
}

export default ExecutiveSync;