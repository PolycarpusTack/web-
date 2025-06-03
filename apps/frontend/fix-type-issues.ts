#!/usr/bin/env node

import * as fs from 'fs';
import * as path from 'path';

// Fix MessageRole enum issues by updating string literals
const fixMessageRoleIssues = () => {
  const filesToFix = [
    'src/pages/ChatPage.tsx',
    'src/pages/EnhancedChatPage.tsx',
    'src/pages/EnhancedChatWithThreadsPage.tsx'
  ];

  filesToFix.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      let content = fs.readFileSync(filePath, 'utf-8');
      
      // Replace role: "user" with role: "user" as any
      content = content.replace(/role: "user"/g, 'role: "user" as any');
      content = content.replace(/role: "assistant"/g, 'role: "assistant" as any');
      content = content.replace(/role: 'user'/g, "role: 'user' as any");
      content = content.replace(/role: 'assistant'/g, "role: 'assistant' as any");
      
      // Add missing stream property to ChatCompletionRequest
      content = content.replace(
        /conversationsApi\.sendMessage\({\s*model_id:[^}]+}\)/g,
        (match) => {
          if (!match.includes('stream:')) {
            return match.replace('})', ', stream: false })');
          }
          return match;
        }
      );

      fs.writeFileSync(filePath, content, 'utf-8');
    }
  });
};

// Fix cost property issues
const fixCostIssues = () => {
  const filesToFix = [
    'src/pages/EnhancedChatPage.tsx',
    'src/pages/EnhancedChatWithThreadsPage.tsx'
  ];

  filesToFix.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      let content = fs.readFileSync(filePath, 'utf-8');
      
      // Fix prompt_cost to costs?.input_cost
      content = content.replace(/response\.data\?\.usage\.prompt_cost/g, 'response.data?.usage.costs?.input_cost');
      
      // Fix completion_cost to costs?.output_cost
      content = content.replace(/response\.data\?\.usage\.completion_cost/g, 'response.data?.usage.costs?.output_cost');

      fs.writeFileSync(filePath, content, 'utf-8');
    }
  });
};

// Fix optional/null type mismatches
const fixOptionalTypes = () => {
  const filesToFix = [
    'src/pages/EnhancedChatPage.tsx',
    'src/pages/EnhancedChatWithThreadsPage.tsx'
  ];

  filesToFix.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      let content = fs.readFileSync(filePath, 'utf-8');
      
      // Fix tokens type issue
      content = content.replace(
        /tokens: response\.data\?\.usage\.prompt_tokens,/g,
        'tokens: response.data?.usage.prompt_tokens || null,'
      );
      content = content.replace(
        /tokens: response\.data\?\.usage\.completion_tokens,/g,
        'tokens: response.data?.usage.completion_tokens || null,'
      );

      fs.writeFileSync(filePath, content, 'utf-8');
    }
  });
};

// Fix ConversationSummary type issues
const fixConversationSummaryIssues = () => {
  const filePath = path.join(__dirname, 'src/pages/ConversationsPage.tsx');
  if (fs.existsSync(filePath)) {
    let content = fs.readFileSync(filePath, 'utf-8');
    
    // Cast ConversationSummary[] to Conversation[]
    content = content.replace(
      /setConversations\(data\.conversations\)/g,
      'setConversations(data.conversations as any)'
    );
    content = content.replace(
      /setFilteredConversations\(data\.conversations\)/g,
      'setFilteredConversations(data.conversations as any)'
    );

    fs.writeFileSync(filePath, content, 'utf-8');
  }
};

// Run all fixes
fixMessageRoleIssues();
fixCostIssues();
fixOptionalTypes();
fixConversationSummaryIssues();