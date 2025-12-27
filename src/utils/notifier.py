# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse

class DingTalkNotifier:
    def __init__(self, token):
        self.token = token
        self.webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={token}"

    def send_text(self, content):
        """
        Send a plain text message.
        """
        if not self.token:
            return

        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        try:
            req = urllib.request.Request(
                url=self.webhook_url, 
                data=json.dumps(data).encode('utf-8'), 
                headers=headers
            )
            context = urllib.request.urlopen(req)
            response = context.read()
            return response
        except Exception as e:
            print(f"DingTalk Notification Error: {e}")
            return None

    def send_markdown(self, title, text):
        """
        Send a markdown message.
        """
        if not self.token:
            return

        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            }
        }
        
        try:
            req = urllib.request.Request(
                url=self.webhook_url, 
                data=json.dumps(data).encode('utf-8'), 
                headers=headers
            )
            context = urllib.request.urlopen(req)
            response = context.read()
            return response
        except Exception as e:
            print(f"DingTalk Notification Error: {e}")
            return None
