#!/usr/bin/env python3
"""
n8n API Helper Script
Create and manage n8n workflows via API
"""

import requests
import json
import sys

class N8NAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-N8N-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
    
    def create_workflow(self, workflow_data):
        """Create a new workflow"""
        url = f"{self.base_url}/api/v1/workflows"
        response = requests.post(url, headers=self.headers, json=workflow_data)
        return response.json()
    
    def update_workflow(self, workflow_id, workflow_data):
        """Update existing workflow"""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}"
        response = requests.put(url, headers=self.headers, json=workflow_data)
        return response.json()
    
    def get_workflow(self, workflow_id):
        """Get workflow by ID"""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def list_workflows(self):
        """List all workflows"""
        url = f"{self.base_url}/api/v1/workflows"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def activate_workflow(self, workflow_id):
        """Activate a workflow"""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/activate"
        response = requests.post(url, headers=self.headers)
        return response.json()
    
    def deactivate_workflow(self, workflow_id):
        """Deactivate a workflow"""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/deactivate"
        response = requests.post(url, headers=self.headers)
        return response.json()
    
    def delete_workflow(self, workflow_id):
        """Delete a workflow"""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}"
        response = requests.delete(url, headers=self.headers)
        return response.json()
    
    def execute_workflow(self, workflow_id, data=None):
        """Execute a workflow"""
        url = f"{self.base_url}/api/v1/workflows/{workflow_id}/execute"
        response = requests.post(url, headers=self.headers, json=data or {})
        return response.json()

# Example usage
if __name__ == '__main__':
    # Configuration
    BASE_URL = "https://n8n.smartmillionaire.co.id"
    API_KEY = "YOUR_API_KEY_HERE"
    
    n8n = N8NAPI(BASE_URL, API_KEY)
    
    # Example: Create a simple webhook workflow
    workflow = {
        "name": "Telegram Bot Webhook",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "telegram/webhook",
                    "options": {}
                },
                "name": "Telegram Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": [250, 300],
                "webhookId": "telegram-bot"
            },
            {
                "parameters": {
                    "functionCode": "const msg = items[0].json.message;\nconst chatId = msg.chat.id;\nconst text = msg.text || '';\n\nif (chatId !== 316228407) {\n  return [{json: {response: 'Unauthorized', chatId, isSSH: false}}];\n}\n\nlet response = '';\nlet command = text.trim().toLowerCase();\nlet isSSH = false;\nlet sshCmd = '';\n\nif (command === '/start' || command === '/help') {\n  response = '🤖 *Bot Commands:*\\n/status - Server status\\n/backup - Manual backup DB\\n/health - Health check\\n/restart <service> - Restart service\\n/logs <service> - Show recent logs\\n/help - Show this message';\n} else if (command === '/status') {\n  response = '🔄 Getting server status...';\n  isSSH = true;\n  sshCmd = 'uptime && free -h && df -h /';\n} else if (command === '/backup') {\n  response = '🔄 Starting manual backup...';\n  isSSH = true;\n  sshCmd = '/root/backup_db.sh';\n} else if (command === '/health') {\n  response = '🔄 Running health check...';\n  isSSH = true;\n  sshCmd = '/root/health_check.sh';\n} else if (command.startsWith('/restart ')) {\n  const svc = command.split(' ')[1];\n  response = '🔄 Restarting ' + svc + '...';\n  isSSH = true;\n  sshCmd = 'systemctl restart ' + svc + ' && echo \"Restarted ' + svc + '\"';\n} else if (command.startsWith('/logs ')) {\n  const svc = command.split(' ')[1];\n  response = '🔄 Getting logs for ' + svc + '...';\n  isSSH = true;\n  sshCmd = 'journalctl -u ' + svc + ' -n 20 --no-pager';\n} else {\n  response = '❓ Unknown command. Type /help for commands.';\n}\n\nreturn [{json: {response, chatId, command, isSSH, sshCmd}}];"
            },
            "name": "Parse Command",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": [470, 300]
        },
        {
            "parameters": {
                "conditions": {
                    "boolean": [
                        {
                            "value1": "={{ $json.isSSH }}",
                            "operation": "true"
                        }
                    ]
                }
            },
            "name": "Is SSH Command",
            "type": "n8n-nodes-base.if",
            "typeVersion": 1,
            "position": [470, 150]
        },
        {
            "parameters": {
                "url": "http://localhost:5679/ssh-command",
                "method": "POST",
                "jsonParameters": true,
                "options": {},
                "bodyParametersJson": "{\n  \"sshCmd\": {{ $json.sshCmd }},\n  \"chatId\": {{ $json.chatId }}\n}"
            },
            "name": "Trigger SSH Executor",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [690, 150]
        },
        {
            "parameters": {
                "functionCode": "return [{json: {response: '🔄 Executing command...', chatId: $json.chatId}}];"
            },
            "name": "Notify Executing",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": [910, 150]
        },
        {
            "parameters": {
                "url": "https://api.telegram.org/bot8871187293:AAGk2B5LI64z9xlxmBi3zXG0EQnJwZIKI3Y/sendMessage",
                "method": "POST",
                "jsonParameters": true,
                "options": {},
                "bodyParametersJson": "{\n  \"chat_id\": {{ $json.chatId }},\n  \"text\": {{ $json.response }},\n  \"parse_mode\": \"Markdown\"\n}"
            },
            "name": "Send Reply",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [690, 300]
        }
    ],
    "connections": {
        "Telegram Webhook": {
            "main": [[{"node": "Parse Command", "type": "main", "index": 0}]]
        },
        "Parse Command": {
            "main": [
                [{"node": "Is SSH Command", "type": "main", "index": 0}],
                [{"node": "Send Reply", "type": "main", "index": 0}]
            ]
        },
        "Is SSH Command": {
            "main": [
                [{"node": "Trigger SSH Executor", "type": "main", "index": 0}],
                [{"node": "Send Reply", "type": "main", "index": 0}]
            ]
        },
        "Trigger SSH Executor": {
            "main": [[{"node": "Notify Executing", "type": "main", "index": 0}]]
        },
        "Notify Executing": {
            "main": [[{"node": "Send Reply", "type": "main", "index": 0}]]
        },
        "Send Reply": {
            "main": []
        }
    },
    "settings": {"executionOrder": "v1"}
}
    
    # Create workflow
    result = n8n.create_workflow(workflow)
    print(json.dumps(result, indent=2))