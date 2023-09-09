# Simple example

This is an example from README.md. It runs a bot with a simple command `/task`.
To run the example:

1. Install requirements, using command `pip install -r example/requirements.txt`;
1. Replace `TOKEN` in `__main__.py` with your actual token;
2. Start taskiq workers, by running `taskiq worker example.tkq:broker --fs-discover`;
3. Start the bot, by running `python example`.
