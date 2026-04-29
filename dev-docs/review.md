# Review
## PatterMatcher
- [ ] remove literal_pattern, only allow regex pattern.
- [ ] suggest raise exception if compile failed or at least logging error

## RPABotCore
- [ ] change self.matcher as a dependency injection into the initialization
- [ ] change config as a class not a dict to get more fine control of the options in config
- [ ] move public methods at the begining of class definition after `__init__` function

### _setup_browser
- [ ] `_setup_browser` method, the persist_path(playwright home path) is assumed to be linux path, however this may not be true as it may be other OS system. In `checker.py` the code give 3 versions of pw base path for macos,windows and linux. but here only linux path is assumed. Need to get the correct path from a common place like a helper class that can cache the correct base path so it only needs to calculate once at the beginning of checking env.
- [ ] line 48, whenever `self._playwright` assigned with a start() return, is the original instance in memory properly released or not? is this a memory leak? May need to do a memory profiling.
- [ ] for browser configs like width, headless, they should be a class attrs instead of instant value, and they should be initialized when RPABotCore is initialized, instead of every time read from config dict.
- [ ] `user_agent` value can be a constant value in the module
- [ ] `self._page` will get memory leak or not?

### _navigate_to_feishu
- [ ] in exception handling, should define custom exception classes instead of using if clause

### _run_loop
- [ ] remove monitored_groups setting in config. Change the behavior to the bot only monitor the current opened chat by manual selection
- [ ] The current_group name's retrieval is very important, the code should automatically extract the group name according to user opened chat
- [ ] after getting messages that are not seen before from `_get_messages()` method, the code calls `self.state.is_seen` again which can be removed
- [ ] if match, the code checks is_reacted or not, the logic is not right. Since all messages that come to this line are all marked as unseen messages, they cannot be reacted, so no need to check `is_reacted`.
- [ ] the `self.state.match_count+1` should be run after `self._react` calling
- [ ] need to get the latest message id from the message list.
- [ ] check_interval sleep can be put into a single finally block .

### _navigate_to_group
- [ ] This method may be removed and replaced with a loop waiting for user to open a group chat and then find the chat and returns its group name automatically.
