#!/usr/bin/env node

import fs from 'fs-extra';
import path from 'path';
import yaml from 'js-yaml';
import { fileURLToPath } from 'url';
import chalk from 'chalk';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class ConfigValidator {
  constructor() {
    this.executives = ['cao', 'cfo', 'cio', 'cmo', 'coo', 'ceo', 'cto', 'gc'];
    this.agents = ['agentsmith', 'cloudexter', 'msmanners'];
    this.errors = [];
    this.warnings = [];
  }

  async validateAll() {
    console.log(chalk.blue('🔍 Validating ChittyAIR configurations...\n'));

    // Validate executive configs
    for (const exec of this.executives) {
      await this.validateExecutive(exec);
    }

    // Validate agent configs
    for (const agent of this.agents) {
      await this.validateAgent(agent);
    }

    // Validate sync permissions
    await this.validateSyncPermissions();

    // Report results
    this.reportResults();
  }

  async validateExecutive(executive) {
    const configPath = path.join(__dirname, 'executives', executive, 'config.yml');
    
    if (await fs.pathExists(configPath)) {
      try {
        const content = await fs.readFile(configPath, 'utf8');
        const config = yaml.load(content);
        
        // Validate required fields
        if (!config.name) {
          this.errors.push(`${executive}: Missing required field 'name'`);
        }
        if (!config.type || config.type !== 'executive') {
          this.errors.push(`${executive}: Invalid type (must be 'executive')`);
        }
        if (!config.version) {
          this.warnings.push(`${executive}: Missing version field`);
        }
        
        // Validate memory configuration
        if (config.memory) {
          if (!config.memory.version) {
            this.warnings.push(`${executive}: Memory version not specified`);
          }
          if (config.memory.version !== 'v5') {
            this.warnings.push(`${executive}: Using outdated memory version ${config.memory.version}`);
          }
        } else {
          this.errors.push(`${executive}: Missing memory configuration`);
        }
        
        // Validate MCP configuration
        if (!config.mcp || !config.mcp.enabled) {
          this.warnings.push(`${executive}: MCP not enabled`);
        }
        
        console.log(chalk.green(`✅ ${executive} configuration valid`));
      } catch (error) {
        this.errors.push(`${executive}: Invalid YAML - ${error.message}`);
      }
    } else {
      console.log(chalk.yellow(`⏭️  ${executive} configuration not found`));
    }
  }

  async validateAgent(agent) {
    const configPath = path.join(__dirname, 'agents', agent, 'config.yml');
    
    if (await fs.pathExists(configPath)) {
      try {
        const content = await fs.readFile(configPath, 'utf8');
        const config = yaml.load(content);
        
        // Validate required fields
        if (!config.name) {
          this.errors.push(`${agent}: Missing required field 'name'`);
        }
        if (!config.type || config.type !== 'agent') {
          this.errors.push(`${agent}: Invalid type (must be 'agent')`);
        }
        
        // Agent-specific validations
        if (agent === 'agentsmith' && !config.monitoring) {
          this.warnings.push(`${agent}: Missing monitoring configuration`);
        }
        if (agent === 'cloudexter' && !config.chaos) {
          this.warnings.push(`${agent}: Missing chaos testing configuration`);
        }
        
        console.log(chalk.green(`✅ ${agent} configuration valid`));
      } catch (error) {
        this.errors.push(`${agent}: Invalid YAML - ${error.message}`);
      }
    } else {
      console.log(chalk.yellow(`⏭️  ${agent} configuration not found`));
    }
  }

  async validateSyncPermissions() {
    const permissionsPath = path.join(__dirname, 'sync-permissions.yml');
    
    if (await fs.pathExists(permissionsPath)) {
      try {
        const content = await fs.readFile(permissionsPath, 'utf8');
        const permissions = yaml.load(content);
        
        // Validate permission structure
        if (!permissions.executives || !permissions.agents) {
          this.errors.push('sync-permissions: Missing executives or agents section');
        }
        
        console.log(chalk.green('✅ Sync permissions valid'));
      } catch (error) {
        this.errors.push(`sync-permissions: Invalid YAML - ${error.message}`);
      }
    } else {
      this.warnings.push('sync-permissions.yml not found');
    }
  }

  reportResults() {
    console.log('\n' + chalk.blue('📊 Validation Results:'));
    
    if (this.errors.length === 0 && this.warnings.length === 0) {
      console.log(chalk.green('\n✅ All configurations are valid!'));
      process.exit(0);
    }
    
    if (this.errors.length > 0) {
      console.log(chalk.red(`\n❌ Found ${this.errors.length} errors:`));
      this.errors.forEach(error => console.log(chalk.red(`   - ${error}`)));
    }
    
    if (this.warnings.length > 0) {
      console.log(chalk.yellow(`\n⚠️  Found ${this.warnings.length} warnings:`));
      this.warnings.forEach(warning => console.log(chalk.yellow(`   - ${warning}`)));
    }
    
    process.exit(this.errors.length > 0 ? 1 : 0);
  }
}

// Run validation
const validator = new ConfigValidator();
await validator.validateAll();