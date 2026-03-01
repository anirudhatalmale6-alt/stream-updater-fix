import requests
import json

class xaccel():

    def create_stream(self, stream_name, profile_id, url, stream_headers=None, video_map=None, audio_map=None, subtitle_map=None, rate_emulation='no'):
    
        headers = {
            'Authorization': 'token ' + self.token,
        }

        json_data = {
            'name': stream_name,
            'input_urls': [
                url,
            ],
            'profile_id': profile_id,
            'rate_emulation': rate_emulation,
            'video_encoders': [
                {
                    'codec': 'copy',
                },
            ],
            'audio_encoders': [
                {
                    'codec': 'copy',
                },
            ],
            'outputs': [
                {
                    'protocol': 'hls',
                    'filename': 'index.m3u8',
                },
                {
                    'protocol': 'http',
                    'filename': 'index.ts',
                }
            ],
        }
        
        if self.proxy is not None:
            json_data['http_proxy'] = self.proxy
            json_data['proxy'] = [self.proxy]
            
        if self.user_agent is not None:
            json_data['user_agent'] = self.user_agent
            
        if stream_headers is not None:
            json_data['headers'] = stream_headers
            
        if video_map is not None:
            json_data['video_map'] = video_map
        
        if audio_map is not None:
            json_data['audio_map'] = audio_map
            
        if subtitle_map is not None:
            json_data['subtitle_map'] = subtitle_map

        response = requests.post(f'{self.base_url}/api/stream/add', headers=headers, json=json_data)

        return response.content.decode()
        
    def get_stream_config(self, stream_name):
        headers = {
            'Authorization': 'token ' + self.token,
        }

        response = requests.get(f'{self.base_url}/api/stream/{stream_name}/config', headers=headers)
        
        data = json.loads(response.content)
        
        return data
        
    def update_stream_header(self, stream_name, header):
        headers = {
            'Authorization': 'token ' + self.token,
        }

        json_data = {
            'headers': header
        }

        response = requests.post(f'{self.base_url}/api/stream/{stream_name}/update', headers=headers, json=json_data)
        
        #data = json.loads(response.content)
        
        #return data
        
    def update_stream_source(self, stream_name, url):
        headers = {
            'Authorization': 'token ' + self.token,
        }

        json_data = [
            url,
        ]

        response = requests.post(f'{self.base_url}/api/stream/{stream_name}/dynamic-url', headers=headers, json=json_data)

        return response.content.decode()

    def update_stream_source_with_restart(self, stream_name, url):
        headers = {
            'Authorization': 'token ' + self.token,
        }

        json_data = [
            url,
        ]

        response = requests.post(f'{self.base_url}/api/stream/{stream_name}/source-update-with-restart', headers=headers, json=json_data)

        return response.content.decode()
        
    def delete_stream(self, stream_name):
        headers = {
            'Authorization': 'token ' + self.token,
        }

        response = requests.post(f'{self.base_url}/api/stream/{stream_name}/delete', headers=headers)
        
        print(response)
        print(response.content)
        
    def fetch_stream_stats(self):
        headers = {
            'Authorization': 'token ' + self.token,
        }

        response = requests.get(f'{self.base_url}/api/stream/stats', headers=headers)
        
        data = json.loads(response.content)
        
        self.stream_stats = data
        
        return data
        
    def get_stream_stats(self, stream_name):

        data = self.stream_stats
        
        for s in data:
            if s['name'].lower() == stream_name.lower():
                return s
                
    def start_stream(self, stream_id):

        headers = {
            'Authorization': 'Token ' + self.token,
        }

        response = requests.post(f'{self.base_url}/api/stream/{stream_id}/start', headers=headers)
        
        return response.content.decode()
        
    def stop_stream(self, stream_id):

        headers = {
            'Authorization': 'Token ' + self.token,
        }

        response = requests.post(f'{self.base_url}/api/stream/{stream_id}/stop', headers=headers)
        
        return response.content.decode()
        
    def restart_stream(self, stream_id):
        self.stop_stream(stream_id)
        self.start_stream(stream_id)
        
    def change_keys(self, stream_id, keys):
        headers = {
            'Authorization': 'Token ' + self.token,
            'Content-Type': 'application/json',
        }

        # Convert keys from "KID:KEY" string format to API JSON format
        key_data = []
        for key in keys:
            if ':' in key:
                parts = key.split(':')
                key_data.append({'kid': parts[0], 'key': parts[1]})

        if not key_data:
            return

        response = requests.post(f'{self.base_url}/api/stream/{stream_id}/decryption-key-update', headers=headers, json=key_data)

        print(f'Key update for {stream_id}: {response.status_code} - {response.content.decode()}')

        return response.content.decode()
        
    def do_stream(self, stream_name, profile_id, url, keys=None, header=None, video_map=None, audio_map=None, subtitle_map=None, rate_emulation='no'):
        cs = self.create_stream(stream_name, profile_id, url, header, video_map, audio_map, subtitle_map, rate_emulation)

        if 'error' in cs:
            cs = json.loads(cs)
            if 'exists' in cs['error']:
                self.start_stream(stream_name)
                uss = self.update_stream_source(stream_name, url)

                if 'error' in uss:
                    uss = json.loads(uss)
                    print(uss['error'])
                else:
                    if header is not None:
                        self.update_stream_header(stream_name, header)
                    print(f'Updated {stream_name} (restarted with new source)')
            else:
                print(cs['error'])
                quit()
        else:
            print(f'Created {stream_name}')

            self.restart_stream(stream_name)
        
    def set_proxy(self, proxy):
        self.proxy = proxy
        
    def set_user_agent(self, user_agent):
        self.user_agent = user_agent
            
    def __init__(self, base_url, token, proxy=None, user_agent=None):
        self.base_url = base_url
        self.token = token
        self.proxy = proxy
        self.user_agent = user_agent