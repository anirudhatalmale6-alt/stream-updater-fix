from pywidevine.cdm import Cdm
from pywidevine.device import Device
from pywidevine.pssh import PSSH
from bs4 import BeautifulSoup
import requests
import pwinput
import base64
import re
import uuid
import json
import os
import threading

requests.packages.urllib3.disable_warnings()

class MagentaTVGoMK():
    def ascii_clear(self):
        os.system('cls||clear')
        print("""
                JJ       JJJ     JJJ       JYYYJ     JJJJJJJ  JJJ    JJJ JJJJJJJJJ    JJ                
               5@@G     5&@B    J&@&5    YB&&&&@#P  P@&&&&&#  #@&5   #@G B&&&&&&&&J  B@@P               
               5@@@B   5@@@B    B@&@&J  Y@@BJ  5BBY P@@YJJJJ  &@@@P  #@B JJJB@&YJJ  P@&@@Y              
               5@@#@#JP@&&@B   P@&JB@B  G@&J  55YYY P@@#B##P  &@B#@B #@B    G@&    Y@@YP@&J             
               5@@YP@&@#J#@B  Y@@#PG@@P G@@J  BB@@B P@@P555Y  &@G G@#&@B    G@&    &@&PG@@B             
               5@@Y P@B  #@B  &@#BBBB@@YJ&@&5YYG@@Y P@@PY55Y  &@G  P@@@B    G@&   B@&BBBB@@P            
               Y##J      G#G 5#B     G#G  PB&&&#GJ  5######B  B#P   5##P    P#B  Y##J    5#B            
                                                                                                        
                                                                                                        
                                                                                                        
               JBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBG   JBBBBBBBBBY                   5BBBBBBBBG            
               5@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@    #@@@@@@@@#                  Y@@@@@@@@@G            
               5@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&    J&@@@@@@@@G                 #@@@@@@@@#             
               5@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&     5@@@@@@@@@Y               P@@@@@@@@@J             
                YYYYYYYYYYYY#@@@@@@@@GYYYYYYYYYYY      B@@@@@@@@#              J@@@@@@@@@P              
                            #@@@@@@@@5                  &@@@@@@@@P             #@@@@@@@@B               
                            #@@@@@@@@5                  Y@@@@@@@@@J           P@@@@@@@@&                
                            #@@@@@@@@5                   G@@@@@@@@#          J&@@@@@@@@5                
                            #@@@@@@@@5                    &@@@@@@@@P         B@@@@@@@@B                 
                            #@@@@@@@@5                    Y@@@@@@@@@        5@@@@@@@@&                  
                            #@@@@@@@@5                     P@@@@@@@@B       &@@@@@@@@Y                  
                            #@@@@@@@@5                      #@@@@@@@@5     B@@@@@@@@G                   
                            #@@@@@@@@5                      J@@@@@@@@&    Y@@@@@@@@#                    
                            #@@@@@@@@5                       P@@@@@@@@B   &@@@@@@@@J                    
                            #@@@@@@@@5                        B@@@@@@@@Y G@@@@@@@@P                     
                            #@@@@@@@@5                         &@@@@@@@&P@@@@@@@@#                      
                            #@@@@@@@@Y                         5@@@@@@@@@@@@@@@@@                       
                            #@@@@@@@@Y                          B@@@@@@@@@@@@@@@5                       
                            #@@@@@@@@Y                           &@@@@@@@@@@@@@B                        
                            #@@@@@@@@Y                           Y@@@@@@@@@@@@&                         
                            #@@@@@@@@Y                            G@@@@@@@@@@@Y                         
                            #@@@@@@@@Y                             &@@@@@@@@@G                          
                            JYYYYYYYY                               YYYYYYYYY                          
                             
                                             Stream updater
                                                                
    """)
    
    def do_cdm(self, pssh, session_id, service_collection_id, media_id, owner_uid):
        pssh = PSSH(pssh)

        device = Device.load(self.cdm_path)
        cdm = Cdm.from_device(device)
        session_id = cdm.open()
        challenge = cdm.get_license_challenge(session_id, pssh)
        
        headers = {
            'accept': '*/*',
            'applicationtoken': service_collection_id,
            'authorizationtoken': self.token,
            'azukiimc': 'IMC7.4.0_XX_Dx.x.x_Sx',
            'content-type': 'application/octet-stream',
            'deviceprofile': self.device_profile,
            'origin': 'https://www.magentatv.mk',
            'user-agent': self.user_agent,
        }
        
        params = {
            'mediaId': media_id,
            'ownerUid': owner_uid,
            'sessionId': session_id,
            'enablelowlatency': ''
        }

        licence = requests.post('https://ottapp-appgw-amp-a.proda.dtp.tv3cloud.com//v1/client/get-widevine-license', headers=headers, params=params, data=challenge, proxies=self.proxies)
        
        try:
            licence.raise_for_status()
            
            cdm.parse_license(session_id, licence.content)

            keys = []
            for key in cdm.get_keys(session_id):
                if key.type != 'SIGNING':
                    keys.append(f"{key.kid.hex}:{key.key.hex()}")
                    
            cdm.close(session_id)
            
            return keys
                    
        except:
            print('License request failed')
            print(licence.content)
    
    def get_channels(self):
        headers = {
            'accept': 'application/json, text/plain, */*',
            'app_key': self.app_key,
            'app_version': self.app_version,
            'bff_token': self.token,
            'device-density': 'xhdpi',
            'device-id': self.device_id,
            'device-name': 'Windows - Chrome',
            'origin': 'https://www.magentatv.mk',
            'pragma': 'akamai-x-cache-on,akamai-x-check-cacheable,akamai-x-get-cache-key',
            'tenant': 'tv',
            'user-agent': self.user_agent,
            'x-call-type': 'AUTH_USER',
            'x-request-session-id': str(uuid.uuid4()),
            'x-request-tracking-id': str(uuid.uuid4()),
            'x-tv-flow': 'START_UP',
            'x-tv-step': 'EPG_CHANNEL',
            'x-user-agent': f'web|web|Chrome-143|{self.app_version}|1',
        }

        params = {
            'natco_key': self.natco_key,
            'includeVirtualChannels': 'true',
            'includeSyntheticChannels': 'false',
            'app_language': 'en_mk',
            'natco_code': 'mk',
        }

        response = requests.get('https://tv-mk-prod.yo-digital.com/mk-bifrost/epg/channel', params=params, headers=headers, proxies=self.proxies)
        
        try:
            response.raise_for_status()
            data = json.loads(response.content)
            
            for c in data['channels']:
                for k, v in data['station_service_collection_map'].items():
                    if c['service_collection_id'] == v['id']:
                        c['service_map'] = data['services_map'][v['service_items'][0]['service_id']]
            
            return data['channels']
        except Exception as e:
            print('Failed getting channels')
            print(response.content)
            quit()
    
    def get_single(self, session_id, service_collection_id, media_id, owner_uid):
        headers = {
            'accept': '*/*',
            'applicationtoken': service_collection_id,
            'authorizationtoken': self.token,
            'azukiimc': 'IMC7.4.0_XX_Dx.x.x_Sx',
            'content-type': 'text/plain',
            'deviceprofile': self.device_profile,
            'origin': 'https://www.magentatv.mk',
            'user-agent': self.user_agent,
        }

        params = {
            'mediaId': media_id,
            'ownerUid': owner_uid,
            'sessionId': session_id,
            'enablelowlatency': ''
        }

        data = '{"roll":{"isLive":true,"rightsMode":"LIVE","inhome":"no"}}'

        response = requests.post('https://ottapp-appgw-amp-a.proda.dtp.tv3cloud.com//v1/client/roll', headers=headers, params=params, data=data, proxies=self.proxies)
        
        try:
            data = json.loads(response.content)

            cdn = data['response']['cdns']['cdn'][0]['base_uri']
            path = data['response']['manifest_uri']

            return cdn + '/' + path
        except:
            print('Failed getting single')
            print(response.content)
            return None
    
    def beacon_stop(self, session_id, service_collection_id, media_id, owner_uid):
        headers = {
            'accept': '*/*',
            'applicationtoken': service_collection_id,
            'authorizationtoken': self.token,
            'azukiimc': 'IMC7.4.0_XX_Dx.x.x_Sx',
            'deviceprofile': self.device_profile,
            'origin': 'https://www.magentatv.mk',
            'user-agent': self.user_agent,
        }
        
        params = {
            'mediaId': media_id,
            'ownerUid': owner_uid,
            'sessionId': session_id,
        }

        data = '{"beacon":{"isLive":true,"complete":true,"inhome":"no"}}'

        response = requests.post('https://ottapp-appgw-amp-a.proda.dtp.tv3cloud.com/v1/client/beacons', headers=headers, data=data, params=params, proxies=self.proxies)
    
    def find_wv_pssh_offsets(self, raw: bytes) -> list:
        offsets = []
        offset = 0
        while True:
            offset = raw.find(b'pssh', offset)
            if offset == -1:
                break
            size = int.from_bytes(raw[offset-4:offset], byteorder='big')
            pssh_offset = offset - 4
            offsets.append(raw[pssh_offset:pssh_offset+size])
            offset += size
        return offsets

    def to_pssh(self, content: bytes) -> list:
        wv_offsets = self.find_wv_pssh_offsets(content)
        return [base64.b64encode(wv_offset).decode() for wv_offset in wv_offsets]
        
        
    def init_to_pssh(self, init_url):
        import time as _time
        headers = {
            'accept': '*/*',
            'user-agent': self.user_agent,
            'content-type': 'application/octet-stream',
            'cache-control': 'no-cache, no-store, must-revalidate',
            'pragma': 'no-cache',
        }

        # Cache-bust: add timestamp to bypass CDN cache
        sep = '&' if '?' in init_url else '?'
        cache_bust_url = f'{init_url}{sep}_t={int(_time.time())}'
        response = requests.get(cache_bust_url, headers=headers, proxies=self.proxies, verify=False)

        return self.to_pssh(response.content)

    def get_pssh(self, url):
        try:
            import time as _time
            headers = {
                'accept': '*/*',
                'user-agent': self.user_agent,
                'content-type': 'application/octet-stream',
                'cache-control': 'no-cache, no-store, must-revalidate',
                'pragma': 'no-cache',
            }

            # Cache-bust: add timestamp to bypass CDN cache
            sep = '&' if '?' in url else '?'
            cache_bust_url = f'{url}{sep}_t={int(_time.time())}'
            response = requests.get(cache_bust_url, headers=headers, proxies=self.proxies, verify=False)
            location = response.url
            
            soup = BeautifulSoup(response.content, features="xml")
            
            init = soup.find('SegmentTemplate')['initialization']
            bandwidth = soup.find('Representation')['bandwidth']
            rep_id = soup.find('Representation')['id']
           
            loc_parts = location.split('/')
            loc_parts.pop()
            
            init_url = '/'.join(loc_parts) + '/' + init.replace('$Bandwidth$', bandwidth).replace('$RepresentationID$', rep_id)
            
            return self.init_to_pssh(init_url)[-1]
        except Exception as e:
            pass
    
    def get_all_init_urls(self, url):
        """Get ALL init segment URLs from the DASH manifest (different Representations = different CDN cache entries)."""
        try:
            import time as _time
            headers = {
                'accept': '*/*',
                'user-agent': self.user_agent,
                'cache-control': 'no-cache, no-store, must-revalidate',
                'pragma': 'no-cache',
            }
            sep = '&' if '?' in url else '?'
            cache_bust_url = f'{url}{sep}_t={int(_time.time())}'
            response = requests.get(cache_bust_url, headers=headers, proxies=self.proxies, verify=False)
            location = response.url

            soup = BeautifulSoup(response.content, features="xml")

            loc_parts = location.split('/')
            loc_parts.pop()
            base_url = '/'.join(loc_parts)

            init_urls = []
            for seg_template in soup.find_all('SegmentTemplate'):
                init_pattern = seg_template.get('initialization', '')
                if not init_pattern:
                    continue
                parent = seg_template.parent
                for rep in parent.find_all('Representation'):
                    bandwidth = rep.get('bandwidth', '')
                    rep_id = rep.get('id', '')
                    init_url = base_url + '/' + init_pattern.replace('$Bandwidth$', bandwidth).replace('$RepresentationID$', rep_id)
                    if init_url not in init_urls:
                        init_urls.append(init_url)

            return init_urls
        except Exception as e:
            return []

    def get_media_segment_urls(self, url):
        """Get live media segment URLs from DASH manifest. Media segments are NOT cached like init segments."""
        try:
            import time as _time
            headers = {
                'accept': '*/*',
                'user-agent': self.user_agent,
                'cache-control': 'no-cache, no-store, must-revalidate',
                'pragma': 'no-cache',
            }
            sep = '&' if '?' in url else '?'
            cache_bust_url = f'{url}{sep}_t={int(_time.time())}'
            response = requests.get(cache_bust_url, headers=headers, proxies=self.proxies, verify=False)
            location = response.url

            soup = BeautifulSoup(response.content, features="xml")

            loc_parts = location.split('/')
            loc_parts.pop()
            base_url = '/'.join(loc_parts)

            media_urls = []
            for seg_template in soup.find_all('SegmentTemplate'):
                media_pattern = seg_template.get('media', '')
                if not media_pattern:
                    continue
                timeline = seg_template.find('SegmentTimeline')
                if not timeline:
                    continue
                parent = seg_template.parent
                rep = parent.find('Representation')
                if not rep:
                    continue
                bandwidth = rep.get('bandwidth', '')
                rep_id = rep.get('id', '')

                # Get the last segment number from timeline
                segments = timeline.find_all('S')
                if segments:
                    last_seg = segments[-1]
                    t = last_seg.get('t', '')
                    if t:
                        media_url = base_url + '/' + media_pattern.replace('$Bandwidth$', bandwidth).replace('$RepresentationID$', rep_id).replace('$Time$', t)
                        media_urls.append(media_url)

            return media_urls
        except Exception as e:
            return []

    def get_pssh_from_media_segment(self, url):
        """Extract PSSH from live media segments (moof boxes). During key rotation,
        the packager may embed the new PSSH with new KID in media segments."""
        media_urls = self.get_media_segment_urls(url)
        headers = {
            'accept': '*/*',
            'user-agent': self.user_agent,
            'cache-control': 'no-cache',
        }
        for media_url in media_urls[:2]:  # Try first 2 media segments
            try:
                response = requests.get(media_url, headers=headers, proxies=self.proxies, verify=False, timeout=10)
                if response.status_code == 200 and len(response.content) > 100:
                    psshs = self.to_pssh(response.content)
                    if psshs:
                        print('  Found PSSH in media segment!')
                        return psshs[-1]
            except Exception:
                pass
        return None

    def get_pssh_aggressive(self, url, old_keys=None):
        """Aggressively try to find fresh PSSH. Tries media segments first (not cached),
        then all init segment URLs (different CDN cache entries)."""
        # Strategy 1: Try MEDIA SEGMENTS first (most likely to have fresh PSSH during key rotation)
        try:
            media_pssh = self.get_pssh_from_media_segment(url)
            if media_pssh:
                return media_pssh, url
        except Exception:
            pass

        # Strategy 2: Try ALL init segment URLs (different Representations = different cache entries)
        init_urls = self.get_all_init_urls(url)
        for init_url in init_urls:
            try:
                psshs = self.init_to_pssh(init_url)
                if psshs:
                    return psshs[-1], url
            except Exception:
                pass

        # Strategy 3: Fall back to default single init URL
        pssh = self.get_pssh(url)
        return pssh, url

    def get_init_values(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'User-Agent': self.user_agent,
        }

        response = requests.get('https://www.magentatv.mk/', headers=headers, proxies=self.proxies)
        
        try:
            response.raise_for_status()
            
            for line in response.content.decode().splitlines():
                if 'window.APP_CONSTANTS' in line:
                    app_constants = json.loads(re.sub(r'new Date\("([^"]+)"\)', r'"\1"', line.strip().strip('window.APP_CONSTANTS').strip().strip('=').strip().replace('undefined', 'null')))
            
            return app_constants['NATCO_KEY'], app_constants['CMS_CONFIGURATION_API_KEY'], app_constants['APP_VERSION']
            
        except Exception as e:
            print('Failed getting init values')
            print(response.content)
            print(e)
            quit()
    
    def init_login(self, session, device_id):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'User-Agent': self.user_agent,
        }

        params = {
            'tenant': 'mkt001',
            'deviceId': device_id,
            'deviceTypeV2': '',
            'deviceType': '',
            'response_type': 'token',
            'redirect_uri': 'https://www.magentatv.mk/?redirectUrl=/?end=1?oauth=genericendusers&tenant=mkt001#2btbf5nph6y',
        }

        response = session.get('https://ottapp-appgw-client-a.proda.dtp.tv3cloud.com/Red/sts/oauth/signin/GENERICENDUSERS', headers=headers, params=params, proxies=self.proxies)
        
        try:
            response.raise_for_status()
            soup = BeautifulSoup(response.content, features='xml')
            
            return soup.find('input', {'name': '__RequestVerificationToken'})['value'], soup.find('form')['action']
        except Exception as e:
            print('Failed init login')
            print(response.content)
            print(e)
            quit()

    def do_login(self, session, request_verification_token, form_action, username, password):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://id.telekom.mk',
            'Referer': 'https://id.telekom.mk' + form_action,
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.user_agent,
        }

        data = {
            '__RequestVerificationToken': request_verification_token,
            'ApplicationId': '34',
            'postLanguage': '',
            'UserName': username,
            'Password': password,
            'singlebutton': '',
        }

        response = session.post('https://id.telekom.mk' + form_action, headers=headers, data=data, proxies=self.proxies)

        try:
            cookies = session.cookies.get_dict()

            return cookies['access-token'], cookies['oauth']
        except Exception as e:
            print('Failed logging in')
            print(response.url)
            print(e)
            quit()
    
    def take_existing_device_id(self, token, device_id):
        headers = {
            'accept': 'application/json, text/plain, */*',
            'app_key': self.app_key,
            'app_version': self.app_version,
            'bff_token': token,
            'device-density': 'xhdpi',
            'device-id': device_id,
            'device-name': 'Windows - Chrome',
            'origin': 'https://www.magentatv.mk',
            'pragma': 'akamai-x-cache-on,akamai-x-check-cacheable,akamai-x-get-cache-key',
            'tenant': 'tv',
            'user-agent': self.user_agent,
            'x-call-type': 'AUTH_USER',
            'x-request-session-id': str(uuid.uuid4()),
            'x-request-tracking-id': str(uuid.uuid4()),
            'x-tv-flow': 'START_UP',
            'x-tv-step': 'EPG_CHANNEL',
            'x-user-agent': f'web|web|Chrome-143|{self.app_version}|1',
        }

        params = {
            'filter_enabled': 'true',
            'app_language': 'mk',
            'natco_code': 'mk',
        }

        response = requests.get('https://tv-mk-prod.yo-digital.com/mk-bifrost/setting/devices', params=params, headers=headers, proxies=self.proxies)
        
        try:
            data = json.loads(response.content)
            
            return data['devices'][0]['id']
        except:
            return device_id
    
    def do_refresh(self, refresh_token, device_id):
        session = requests.Session()

        cookies = {
            'provider': 'GENERICENDUSERS',
            'response_type': 'token',
            'redirect_uri': 'https%3A%2F%2Fwww.magentatv.mk%2F%3FredirectUrl%3D%2F%3Fend%3D1%3Foauth%3Dgenericendusers%26tenant%3Dmkt001%232btbf5nph6y',
            'oauth': refresh_token,
        }

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'User-Agent': self.user_agent,
        }

        params = {
            'tenant': 'mkt001',
            'deviceId': device_id,
            'deviceTypeV2': '',
            'deviceType': '',
            'response_type': 'token',
            'redirect_uri': 'https://www.magentatv.mk/?redirectUrl=/?end=1?oauth=genericendusers&tenant=mkt001#2btbf5nph6y',
        }

        response = session.get('https://ottapp-appgw-client-a.proda.dtp.tv3cloud.com/Red/sts/oauth/signin/GENERICENDUSERS', params=params, cookies=cookies, headers=headers, proxies=self.proxies)
        
        cookies = session.cookies.get_dict()
        
        return cookies['access-token'], cookies['oauth']
    
    def get_token(self):
        """Thread-safe token refresh. Uses a lock to prevent concurrent threads
        from consuming the single-use OAuth refresh token simultaneously."""
        with self._token_lock:
            return self._get_token_unsafe()

    def _get_token_unsafe(self):
        try:
            f = open('auth.json', 'r')
            auth = json.loads(f.read())
            f.close()

            refresh_token = auth['refresh_token']
            device_id = auth['device_id']

            token, refresh_token = self.do_refresh(refresh_token, device_id)
            existing_device_id = self.take_existing_device_id(token, device_id)
            if device_id != existing_device_id:
                device_id = existing_device_id
                token, refresh_token = self.do_refresh(refresh_token, device_id)

            f = open('auth.json', 'w')
            f.write(json.dumps({
                'refresh_token': refresh_token,
                'device_id': device_id,
            },indent=2))
            f.close()

            return token, device_id

        except Exception as e:
            pass

        is_saved_credentials_login = False

        try:
            f = open('creds.json', 'r')
            creds = json.loads(f.read())
            f.close()

            username = creds['username']
            password = creds['password']
            is_saved_credentials_login = True
        except:
            self.ascii_clear()
            print('Please log-in')
            username = input('\nEnter username: ')
            password = pwinput.pwinput()

        session = requests.Session()
        device_id = str(uuid.uuid4())
        request_verification_token, form_action = self.init_login(session, device_id)
        token, refresh_token = self.do_login(session, request_verification_token, form_action, username, password)
        existing_device_id = self.take_existing_device_id(token, device_id)
        if device_id != existing_device_id:
            try:
                token, refresh_token = self.do_refresh(refresh_token, existing_device_id)
            except:
                print('Failed refresh on login')
                return None, None

        f = open('auth.json', 'w')
        f.write(json.dumps({
            'refresh_token': refresh_token,
            'device_id': device_id
        },indent=2))
        f.close()

        if not is_saved_credentials_login:
            self.ascii_clear()
            choice = input('Save credentials? (y or n): ')

            if choice.lower() == 'y':
                f = open('creds.json', 'w')
                f.write(json.dumps({
                    'username': username,
                    'password': password,
                }, indent=2))
                f.close()

        return token, device_id
    
    def get_stream(self, stream, old_keys=None, max_attempts=1):
        """Get stream data. If old_keys provided and max_attempts > 1,
        tries multiple CDN sessions to find fresh keys faster.
        Uses aggressive PSSH extraction (media segments + all init URLs)."""
        token_result = self.get_token()
        if not token_result or not token_result[0]:
            return None
        self.token, self.device_id = token_result

        service_collection_id = stream['service_collection_id']
        media_id = stream['service_map']['media_id']
        owner_uid = stream['service_map']['owner_id']

        best_result_keys = None
        best_result_url = None

        for attempt in range(max_attempts):
            session_id = str(uuid.uuid4())

            url = self.get_single(session_id, service_collection_id, media_id, owner_uid)
            if not url:
                continue

            # On retry attempts, also try wv3 device profile
            if attempt > 0 and attempt % 2 == 0:
                url = url.replace('wv1', 'wv3')

            # Use aggressive PSSH: media segments first, then all init URLs
            pssh, pssh_url = self.get_pssh_aggressive(url, old_keys=old_keys)
            if pssh:
                keys = self.do_cdm(pssh, session_id, service_collection_id, media_id, owner_uid)
                if keys:
                    best_result_keys = keys
                    best_result_url = url

                    # If we found different keys from old ones, use them immediately
                    if old_keys and keys != old_keys:
                        print(f'  Found fresh keys on attempt {attempt + 1}')
                        self.beacon_stop(session_id, service_collection_id, media_id, owner_uid)
                        break

            self.beacon_stop(session_id, service_collection_id, media_id, owner_uid)

        if best_result_url:
            # Use the original wv1 URL for XAccel (not wv3)
            stream['url'] = best_result_url.replace('wv3', 'wv1')
        if best_result_keys:
            stream['keys'] = best_result_keys

        return stream if best_result_url else None
    
    def get_title(self, obj):
        return obj['title']
    
    def __init__(self, config):
        self.config = config
        for key, value in config.items():
            setattr(self, key, value)
        self.proxies = {'https': config['proxy'], 'http': config['proxy']}
        self.cdm_path = f'../../cdms/{config["cdm_file_name"]}'
        self._token_lock = threading.Lock()

        self.natco_key, self.app_key, self.app_version = self.get_init_values()

        self.token, self.device_id = self.get_token()

        self.device_profile = base64.b64encode(json.dumps({"model":"Desktop","osVersion":"10","vendorName":"Microsoft","osName":"HTML5","deviceUUID":self.device_id,"wvLevel":"L3"}, separators=(',', ':')).encode('utf-8')).decode('utf-8')
