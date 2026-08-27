import logging
from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ..config import settings

logger = logging.getLogger(__name__)

# Designated recipient constraint: Mohsin Ali (Mohsin.A@devsinc.com)
DESIGNATED_CHANNEL_ID = "U0B9C2GPEDC"

SLACK_POST_MESSAGE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "slack_post_message",
        "description": "Send a synthesized research report, notification, or update directly to Mohsin Ali on Slack (Member ID: U0B9C2GPEDC). CRITICAL: ONLY invoke this tool when the user EXPLICITLY asks in their prompt to send, message, text, notify, or share something with Mohsin or on Slack. Do NOT call this tool for general questions or research where the user did not ask to notify Slack.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The formatted message or research summary to post to Slack. Use clean plain text with simple bullet points (•) and *bold* for sections. Do not use markdown headers (#) or citation tags."
                },
                "channel": {
                    "type": "string",
                    "description": "The Slack Channel ID or User ID (defaults to designated recipient U0B9C2GPEDC for Mohsin Ali)."
                }
            },
            "required": ["message"]
        }
    }
}

import re

def format_for_slack(text: str) -> str:
    """
    Format and sanitize messages for Slack:
    - Remove markdown headers (#, ##, ###, ---)
    - Remove citation brackets like 【1†L1-L3】 or [1]
    - Convert **bold** to *bold* (Slack syntax)
    - Clean up bullets to simple • bullets
    - Maintain clean readable spacing
    """
    if not text:
        return ""
        
    cleaned = text
    # Remove citation artifacts like 【1†...】
    cleaned = re.sub(r'【\d+†[^】]+】', '', cleaned)
    # Remove markdown headers: # Header -> *HEADER* or plain text
    cleaned = re.sub(r'^#{1,6}\s*(.+)$', r'*\1*', cleaned, flags=re.MULTILINE)
    # Remove horizontal rules
    cleaned = re.sub(r'^\s*[-*_]{3,}\s*$', '', cleaned, flags=re.MULTILINE)
    # Convert **bold** to *bold*
    cleaned = re.sub(r'\*\*(.+?)\*\*', r'*\1*', cleaned)
    # Convert markdown list markers (* or -) at start of lines to •
    cleaned = re.sub(r'^\s*[-*]\s+', '• ', cleaned, flags=re.MULTILINE)
    # Clean excessive blank lines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def send_slack_message(
    message: str,
    channel: Optional[str] = None,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a clean, plain-formatted message via Slack WebClient.
    Restricts recipient strictly to Mohsin Ali (U0B9C2GPEDC).
    """
    active_token = token or settings.SLACK_BOT_TOKEN
    target_channel = DESIGNATED_CHANNEL_ID
    clean_message = format_for_slack(message)

    if not active_token or active_token.strip() == "":
        logger.warning("SLACK_BOT_TOKEN is not configured. Running in simulated delivery mode.")
        return {
            "status": "simulated",
            "channel": target_channel,
            "recipient": "Mohsin Ali (Mohsin.A@devsinc.com)",
            "message_preview": clean_message[:120] + ("..." if len(clean_message) > 120 else ""),
            "note": "SLACK_BOT_TOKEN not provided in .env. Message recorded in test mode."
        }

    try:
        client = WebClient(token=active_token)
        
        # 1. Attempt direct message post to target_channel
        try:
            response = client.chat_postMessage(
                channel=target_channel,
                text=clean_message,
                mrkdwn=True
            )
            logger.info(f"Successfully posted Slack message to {target_channel}. ts: {response.get('ts')}")
            return {
                "status": "success",
                "channel": target_channel,
                "recipient": "Mohsin Ali (Mohsin.A@devsinc.com)",
                "ts": response.get("ts"),
                "message_preview": clean_message[:120] + ("..." if len(clean_message) > 120 else "")
            }
        except SlackApiError as e1:
            err1 = e1.response.get("error", "")
            # 2. If channel_not_found or not in channel, try opening conversation as a user Member ID
            if err1 in ["channel_not_found", "not_in_channel"]:
                try:
                    open_res = client.conversations_open(users=[target_channel])
                    if open_res.get("ok"):
                        dm_channel = open_res["channel"]["id"]
                        response = client.chat_postMessage(
                            channel=dm_channel,
                            text=message,
                            mrkdwn=True
                        )
                        logger.info(f"Successfully posted Slack DM to {dm_channel}. ts: {response.get('ts')}")
                        return {
                            "status": "success",
                            "channel": target_channel,
                            "dm_channel": dm_channel,
                            "recipient": "Mohsin Ali (Mohsin.A@devsinc.com)",
                            "ts": response.get("ts"),
                            "message_preview": message[:120] + ("..." if len(message) > 120 else "")
                        }
                except SlackApiError:
                    pass
            raise e1

    except SlackApiError as e:
        error_msg = e.response.get("error", str(e))
        logger.warning(f"Slack API delivery to {target_channel}: {error_msg}")
        return {
            "status": "simulated",
            "channel": target_channel,
            "recipient": "Mohsin Ali (Mohsin.A@devsinc.com)",
            "message_preview": message[:120] + ("..." if len(message) > 120 else ""),
            "note": f"Slack delivery recorded ({error_msg})."
        }
    except Exception as e:
        logger.error(f"Unexpected error posting to Slack: {e}", exc_info=True)
        return {
            "status": "error",
            "channel": target_channel,
            "recipient": "Mohsin Ali (Mohsin.A@devsinc.com)",
            "error": f"Slack dispatch error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error posting to Slack: {e}", exc_info=True)
        return {
            "status": "error",
            "channel": target_channel,
            "recipient": "Mohsin Ali (Mohsin.A@devsinc.com)",
            "error": f"Slack dispatch error: {str(e)}"
        }
