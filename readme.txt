I made a small update to StreamUpdater, I added 2 new command line arguments:

--auto-select-script {SCRIPT_NUMBER_HERE}  (Automatically selects the script from the selection menu)
--auto-start-update (Will automatically start the update mode 2)

You can now use pm2 (or something similar) to run the script instead of tmux.
Example pm2 command:

pm2 start StreamUpdater.py --interpreter python3 -- --auto-start-update --auto-select-script {SCRIPT_NUMBER_HERE}
