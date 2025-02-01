import { SlashCommandBuilder } from 'discord.js';
import { execSync, spawn } from 'child_process';

import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


export const data = new SlashCommandBuilder()
    .setName('calculate')
    .setDescription('Replies with Winnings!');

export async function execute(interaction) {
    await interaction.deferReply();
    try {
        // Pull the latest changes from the repo
        const output = execSync('git pull', { cwd: process.cwd() });
        console.log(output.toString());
    } catch (err) {
        console.error('Error during git pull:',err);
    }

    
    let resultOutput;
    try {
      resultOutput = await new Promise((resolve, reject) => {
        // Spawn the python process
        const pythonProcess = spawn('poetry', ['run', 'python', 'main.py']);
        let output = '';
        
        // Collect the output from the python process
        pythonProcess.stdout.on('data', (data) => {
          output += data.toString();
        });
        
        // Resolve the promise once the process closes.
        pythonProcess.on('close', () => {
          resolve(output);
        });
        
        // Reject the promise if an error occurs.
        pythonProcess.on('error', (err) => {
          reject(err);
        });
      });
    } catch (err) {
      console.error('Error running Python script:', err);
      resultOutput = 'There was an error running the Python script.';
    }
    
    // Edit the deferred reply with the final result..
    await interaction.editReply(resultOutput || 'No output from the Python script.');
}