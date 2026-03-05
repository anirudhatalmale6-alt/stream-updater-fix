from waitress import serve
from flask import Flask, redirect, abort, request
import json
import signal
import requests
import os
import logging
import xaccel
import importlib
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def bye(sig=None, frame=None):
    print('\nBye :)')
    quit()

signal.signal(signal.SIGINT, bye)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

class StreamUpdater():
    def ascii_clear(self):
        os.system('cls||clear')
        print("""

  ███████╗████████╗██████╗ ███████╗ █████╗ ███╗   ███╗    ██╗   ██╗██████╗ ██████╗  █████╗ ████████╗███████╗██████╗
  ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗████╗ ████║    ██║   ██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔══██╗
  ███████╗   ██║   ██████╔╝█████╗  ███████║██╔████╔██║    ██║   ██║██████╔╝██║  ██║███████║   ██║   █████╗  ██████╔╝
  ╚════██║   ██║   ██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║    ██║   ██║██╔═══╝ ██║  ██║██╔══██║   ██║   ██╔══╝  ██╔══██╗
  ███████║   ██║   ██║  ██║███████╗██║  ██║██║ ╚═╝ ██║    ╚██████╔╝██║     ██████╔╝██║  ██║   ██║   ███████╗██║  ██║
  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚═════╝ ╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝

                                                   StreamUpdater v0.16
    """)

    def get_config(self):
        try:
            f = open('config.json')
            data = json.load(f)

            return data
        except Exception as e:
            print('Error loading config')
            print(e)
            quit()

    def load_streams(self):
        try:
            f = open('streams.json')
            data = json.load(f)

            self.streams = data
        except Exception as e:
            print('Error loading streams.json')
            print(e)
            quit()

    def store_streams(self):
        try:
            f = open("streams.json", 'w')
            f.write(json.dumps(self.streams, indent=2))
            f.close()
        except Exception as e:
            print('Error storing streams.json')
            print(e)
            quit()

    def root():
        return 'StreamUpdater v0.16'

    def get_stream(self, stream_id):
        try:
            stream_id = int(stream_id)
        except:
            return 'Stream id must be a number', 400

        try:
            stream = self.streams[stream_id]
        except:
            abort(404)

        url = stream['url']

        headers = {
            'user-agent': self.Script.config['user-agent']
        }

        if 'headers' in stream:
            headers.update(stream['headers'])

        r = requests.get(url, headers=headers, proxies=self.Script.proxies)
        if r.status_code != 200:
            name = self.Script.get_title(stream)
            self.logger.info(f' Updating stream: {name}')
            new_stream = self.Script.get_stream(stream)

            if not stream:
                self.logger.info(f' Failed updating stream: {name}')
                return f'Failed updating stream: {name}', 400

            self.logger.info(f' Successfully updated {name}')

            old_stream = stream
            stream.update(new_stream)

            if 'preserve_keys' in self.Script.config and 'keys' in stream and self.Script.config['script_config']:
                stream['keys'] = old_stream['keys']

            self.streams[stream_id] = stream

            self.store_streams()

        url = stream['url']

        if not r:
            r = requests.get(url, headers=headers, proxies=self.Script.proxies)

        if 'keys' in stream:
            if '?' in url:
                url += '&decryption_key='
            else:
                url += '?decryption_key='
            for key in stream['keys']:
                url += f'{key},'
            url = url.strip(',')

        name = self.Script.get_title(stream)

        self.logger.info(f' Stream {name} redirected to {url}')

        return redirect(url, code=302)

    def picker(self, channels, get_title, name='Channel', multiple=True):
        print(f'{name}s:\n')

        i = 1
        for c in channels:
            print(f'{i}. {get_title(c)}')
            i+=1

        if multiple:
            print('\nTo choose more then 1, follow format example: 1-x')

        choose = input(f'\nChoose {name.lower()}: ')

        r = []

        if '-' in choose and multiple:
            choose = choose.split('-')
            n1 = int(choose[0])
            n2 = int(choose[1])

            if(n1 < 1):
                n1 = 1

            if(n2 > len(channels)):
                n2 = len(channels)

            for i in range(n1, n2+1):
                r.append(channels[i-1])
        elif ',' in choose and multiple:
            scns = choose.split(',')
            for sc in scns:
                try:
                    num = int(sc)
                    r.append(channels[num-1])
                except:
                    pass
        else:
            choose = int(choose) - 1
            if choose < 0 or choose > len(channels):
                return self.picker(channels)

            r.append(channels[choose])

        if multiple:
            return r
        else:
            return r[0]

    def manual_selection(self):
            Script = self.Script

            Script.ascii_clear()
            channels = Script.get_channels()
            chosen = self.picker(channels, Script.get_title)

            r = []

            Script.ascii_clear()
            for c in chosen:

                name = Script.get_title(c)

                print('\n' + name)

                o = Script.get_stream(c)

                if o:
                    print('  Manifest url:', o['url'])
                    if 'keys' in o:
                        print('  Keys:')
                        for key in o['keys']:
                            print(f'   - {key}')

                    c.update(o)
                    r.append(c)

            return r

    def get_script_name(self, script_name):
        return script_name

    def run_updater(self):
        stream_stats = self.xaccel.fetch_stream_stats()

        i = 0
        for s in self.streams:
            name = self.Script.get_title(s)
            url = f'{self.base_url}:{self.port}/stream/{str(i)}'

            running = False
            for ss in stream_stats:
                if ss['name'] == self.Script.prefix + name and ss['status'] == 'running':
                    stream_config = self.xaccel.get_stream_config(ss['name'])
                    stream_url = stream_config['input_urls'][0]
                    if str(i) == stream_url:
                        running = True
                        break

            if not running:
                headers = ''
                if 'headers' in s:
                    for k, v in s['headers'].items():
                        headers += f'{k}:{v}\r\n'

                self.xaccel.do_stream(self.Script.prefix + name, self.Script.profile, url, video_map=self.Script.video_map, audio_map=self.Script.audio_map, subtitle_map=self.Script.subtitle_map, rate_emulation=self.Script.rate_emulation, header=headers)

            i += 1

        app = Flask(__name__)

        print(f'\nStarted Stream Updater, listening on port: {self.port}')
        app.add_url_rule("/", view_func=self.root)
        app.add_url_rule("/stream/<stream_id>", view_func=self.get_stream)
        serve(app, host="0.0.0.0", port=self.port)

    def _check_damaged_channel(self, channel_info):
        """Check a single damaged channel for fresh keys. Used for parallel execution."""
        name, c, old_keys, script_config = channel_info
        try:
            stream = self.Script.get_stream(c, old_keys=old_keys, max_attempts=5)

            if not stream:
                return (name, 'failed', None, None)

            if old_keys and 'preserve_keys' in script_config and script_config['preserve_keys']:
                stream['keys'] = old_keys

            new_keys = stream.get('keys', None)
            keys_changed = new_keys is not None and old_keys is not None and new_keys != old_keys

            return (name, 'keys_changed' if keys_changed else 'same_keys', new_keys, stream)
        except Exception as e:
            return (name, 'error', None, None)

    def run_legacy_updater(self):
        script_config = self.Script.config

        for s in self.streams:
            old_keys = None
            if 'keys' in s:
                old_keys = s['keys']

            stream = self.Script.get_stream(s)

            if not stream:
                name = self.Script.get_title(s)
                print(f'Failed to get stream data for {name}, using stored data')
                stream = s  # fall back to stored stream data

            if old_keys and 'preserve_keys' in script_config and script_config['preserve_keys']:
                stream['keys'] = old_keys

            name = self.Script.get_title(stream)
            url = stream['url']

            if 'keys' in stream:
                if '?' in url:
                    url += '&decryption_key='
                else:
                    url += '?decryption_key='
                for key in stream['keys']:
                    url += f'{key},'
                url = url.strip(',')

            headers = ''
            if 'headers' in stream:
                for k, v in stream['headers'].items():
                    headers += f'{k}:{v}\r\n'

            stream_keys = stream.get('keys', None)
            self.xaccel.do_stream(self.Script.prefix + name, self.Script.profile, url, keys=stream_keys, video_map=self.Script.video_map, audio_map=self.Script.audio_map, subtitle_map=self.Script.subtitle_map, rate_emulation=self.Script.rate_emulation, header=headers)

        delay = 30
        if 'delay' in script_config:
            delay = script_config['delay']

        tolerance = 0.8
        if 'tolerance' in script_config:
            tolerance = script_config['tolerance']

        always_update_in_xaccel = False
        if 'always_update_in_xaccel' in script_config:
            always_update_in_xaccel = script_config['always_update_in_xaccel']

        self.ascii_clear()
        channels = self.Script.get_channels()

        channels_updated = 0
        keys_refreshed = 0
        hot_swaps = 0
        checks_made = 1
        restart_cooldowns = {}  # track last restart time per channel
        last_channel_refresh = 0
        while True:
            try:
                # Refresh channel list every 10 minutes to get updated metadata
                if time.time() - last_channel_refresh > 600:
                    try:
                        channels = self.Script.get_channels()
                        last_channel_refresh = time.time()
                        print('Refreshed channel list')
                    except Exception as e:
                        print(f'Failed to refresh channels: {e}')

                stream_stats = self.xaccel.fetch_stream_stats()

                self.ascii_clear()

                print('Channels updated:', channels_updated)
                print('Keys refreshed:', keys_refreshed)
                print('Hot key swaps:', hot_swaps)
                print('Checks made:', checks_made)
                print('')

                # Collect damaged channels for parallel processing
                damaged_channels = []
                normal_channels = []

                for ss in stream_stats:
                    if self.Script.prefix in ss['name']:
                        name = ss['name']

                        is_stopped = ss['status'] == 'stopped'
                        is_broken = (ss['status'] != 'running' and ss['status'] != 'starting' and not is_stopped) and (ss['bitrate'] == 0.0 or ss['speed'] < tolerance)
                        is_running = ss['status'] == 'running'
                        is_damaged = is_running and ss['errors'] > 500

                        if is_damaged:
                            # Find channel data and old keys
                            for c in channels:
                                if self.Script.get_title(c) == name.replace(self.Script.prefix, '').strip():
                                    old_keys = None
                                    for s in self.streams:
                                        if self.Script.get_title(s) == self.Script.get_title(c):
                                            if 'keys' in s:
                                                old_keys = list(s['keys'])  # copy to avoid mutation
                                    damaged_channels.append((name, c, old_keys, ss))
                                    break
                        elif is_broken or is_stopped or always_update_in_xaccel:
                            normal_channels.append((name, ss))
                        else:
                            print(f'{name} - {ss["status"]}')

                # Process normal (broken/stopped) channels sequentially
                for name, ss in normal_channels:
                    is_stopped = ss['status'] == 'stopped'
                    for c in channels:
                        if self.Script.get_title(c) == name.replace(self.Script.prefix, '').strip():
                            try:
                                old_keys = None
                                for s in self.streams:
                                    if self.Script.get_title(s) == self.Script.get_title(c):
                                        if 'keys' in s:
                                            old_keys = list(s['keys'])

                                stream = self.Script.get_stream(c)
                                if not stream:
                                    print(f'{name} - failed to get stream data, skipping')
                                    continue

                                if old_keys and 'preserve_keys' in script_config and script_config['preserve_keys']:
                                    stream['keys'] = old_keys

                                new_keys = stream.get('keys', None)
                                url = stream['url']

                                if 'keys' in stream:
                                    if '?' in url:
                                        url += '&decryption_key='
                                    else:
                                        url += '?decryption_key='
                                    for key in stream['keys']:
                                        url += f'{key},'
                                    url = url.strip(',')

                                headers = ''
                                if 'headers' in stream:
                                    for k, v in stream['headers'].items():
                                        headers += f'{k}:{v}\r\n'

                                self.xaccel.do_stream(name, self.Script.profile, url, keys=new_keys, video_map=self.Script.video_map, audio_map=self.Script.audio_map, subtitle_map=self.Script.subtitle_map, rate_emulation=self.Script.rate_emulation, header=headers)
                                channels_updated += 1
                                if is_stopped:
                                    print(f'{name} - was stopped, started')
                                else:
                                    print(f'{name} - broken, restarted')

                                for s in self.streams:
                                    if self.Script.get_title(s) == self.Script.get_title(c):
                                        s['keys'] = new_keys
                                self.store_streams()

                            except Exception as e:
                                print(f'{name} - error: {e}')
                            break

                # Process damaged channels IN PARALLEL for faster key detection
                if damaged_channels:
                    print(f'\n--- Checking {len(damaged_channels)} damaged channels in parallel ---')

                    # Prepare tasks for parallel execution
                    tasks = []
                    for name, c, old_keys, ss in damaged_channels:
                        tasks.append((name, c, old_keys, script_config))

                    # Use ThreadPoolExecutor to check all damaged channels concurrently
                    # Max 3 workers to avoid overloading the proxy/API
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        futures = {executor.submit(self._check_damaged_channel, task): task for task in tasks}

                        for future in as_completed(futures):
                            task_name = futures[future][0]
                            try:
                                result_name, status, new_keys, stream = future.result()

                                if status == 'keys_changed' and new_keys:
                                    # NEW KEYS! Restart with new URL (keys embedded in URL)
                                    # Note: /decryption-key-update API does NOT work for DASH streams
                                    # Keys must be in the input_urls as ?decryption_key= parameter
                                    url = stream['url']
                                    if 'keys' in stream:
                                        if '?' in url:
                                            url += '&decryption_key='
                                        else:
                                            url += '?decryption_key='
                                        for key in stream['keys']:
                                            url += f'{key},'
                                        url = url.strip(',')
                                    self.xaccel.restart_with_new_url(result_name, url)
                                    keys_refreshed += 1
                                    print(f'{result_name} - NEW KEYS DETECTED, restarted with fresh keys!')

                                    # Update stored keys
                                    for s in self.streams:
                                        for name2, c2, _, _ in damaged_channels:
                                            if name2 == result_name:
                                                if self.Script.get_title(s) == self.Script.get_title(c2):
                                                    s['keys'] = new_keys
                                    self.store_streams()

                                elif status == 'same_keys':
                                    # Keys haven't changed yet - restart with cooldown for non-key damage
                                    last_restart = restart_cooldowns.get(result_name, 0)
                                    if time.time() - last_restart > 300:
                                        # Find stream data for the URL
                                        for name2, c2, old_k, ss2 in damaged_channels:
                                            if name2 == result_name:
                                                url_for_restart = stream['url'] if stream else None
                                                if url_for_restart and 'keys' in stream:
                                                    if '?' in url_for_restart:
                                                        url_for_restart += '&decryption_key='
                                                    else:
                                                        url_for_restart += '?decryption_key='
                                                    for key in stream['keys']:
                                                        url_for_restart += f'{key},'
                                                    url_for_restart = url_for_restart.strip(',')
                                                if url_for_restart:
                                                    self.xaccel.restart_with_new_url(result_name, url_for_restart)
                                                    restart_cooldowns[result_name] = time.time()
                                                    channels_updated += 1
                                                    print(f'{result_name} - damaged (errors={ss2["errors"]}), cooldown restart')
                                                break
                                    else:
                                        remaining = int(300 - (time.time() - restart_cooldowns.get(result_name, 0)))
                                        for name2, _, _, ss2 in damaged_channels:
                                            if name2 == result_name:
                                                print(f'{result_name} - waiting for new keys (errors={ss2["errors"]}, cooldown {remaining}s)')
                                                break

                                elif status == 'failed':
                                    print(f'{result_name} - failed to get stream data')
                                elif status == 'error':
                                    print(f'{result_name} - error during check')

                            except Exception as e:
                                print(f'{task_name} - exception: {e}')

                checks_made += 1

                # Faster checks when channels are damaged (10s vs 30s)
                actual_delay = 10 if damaged_channels else delay
                print(f'\nFinished check, waiting {actual_delay}s' + (' (fast mode - damaged channels detected)' if damaged_channels else ''))
                print('To quit, press CTRL+C')
                time.sleep(actual_delay)
            except Exception as e:
                print(e)

    def __init__(self):
        parser = argparse.ArgumentParser(description="Used to update video streams on X Acceleration Codec.")
        parser.add_argument('--auto-select-script', type=int, help="Selects the script by number on startup")
        parser.add_argument('--auto-start-update', action='store_true', help="Automatically starts mode 2 of the updater")
        args = parser.parse_args()

        self.ascii_clear()
        self.logger = logging.getLogger('StreamUpdater')
        self.config = self.get_config()

        scripts = os.listdir('./scripts')

        if args.auto_select_script:
            script_name = scripts[args.auto_select_script-1]
        else:
            script_name = self.picker(scripts, self.get_script_name, 'Script', False)

        script_directory = f'./scripts/{script_name}'
        os.chdir(script_directory)
        script_config = self.get_config()
        Script = getattr(importlib.import_module(f'scripts.{script_name}.{script_name}'), script_name)
        self.Script = Script(script_config)

        self.Script.ascii_clear()
        print('Mode selection:\n')
        print('1. Manually select streams')

        streams_exist = os.path.isfile('./streams.json')
        if streams_exist:
            print('2. Use streams.json')

        if args.auto_start_update:
            choice = '2'
        else:
            choice = input('\nChoose mode: ')

        if choice == '1':
            self.streams = self.manual_selection()
            self.store_streams()
        elif choice == '2' and streams_exist:
            self.load_streams()

            self.Script.ascii_clear()
            print('Loaded streams from streams.json:')
            out = ''
            for s in self.streams:
                out += f'{self.Script.get_title(s)}, '
            print(out.strip(', '))

        else:
            print('Invalid mode selected')
            quit()

        if args.auto_start_update:
            choice = 'y'
        else:
            choice = input('\nStart Stream Updater (y or n): ')
        if choice.lower() == 'y':
            self.ascii_clear()

            XAccel_token = self.config['xaccel_token']
            XAccel_url = self.config['xaccel_url']
            self.port = self.config['port']
            self.base_url = self.config['base_url']

            proxy = None
            if hasattr(self.Script, 'proxy_in_xaccel'):
                if self.Script.proxy_in_xaccel:
                    proxy = self.Script.proxy_in_xaccel

            if not hasattr(self.Script, 'subtitle_map'):
                self.Script.subtitle_map = 's:0?'

            self.xaccel = xaccel.xaccel(XAccel_url, XAccel_token, user_agent=self.Script.user_agent, proxy=proxy)

            if 'use_legacy' in script_config and script_config['use_legacy']:
                self.run_legacy_updater()
            else:
                self.run_updater()
        else:
            bye()


StreamUpdater()
