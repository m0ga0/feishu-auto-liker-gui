FEISHU_CHAT_URL = "https://www.feishu.cn/messenger"

SELECTORS = {
    "message_wrapper": "[data-element='message-section-left'], [data-element='message-section-right'], .message-section-left, .message-section-right",
    "message_text": ".message-text .text-only, .richTextContainer .text-only, .text-only",
    "reaction_button": ".messageAction__toolbar .toolbar-item.praise",
    "chat_item": ".chat-item, [class*='chat-item'], [class*='session-item']",
    "message_input": ".message-input, [class*='message-input'], [contenteditable='true']",
    "search_input": ".search-input, [class*='search'], [placeholder*='搜索']",
}