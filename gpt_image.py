#!/usr/bin/env python3
# gpt_image.py - ChatGPT (OpenAI) image generation as a subagent for Silk Road art.
# Fadak 8/18, per Kris + Barid's note that a specific script is needed.
#
# SETUP (once):
#   Put your OpenAI API key in ONE of:
#     - environment variable  OPENAI_API_KEY
#     - a file named          openai_key.txt   next to this script (just the key, one line)
#   (Keys come from https://platform.openai.com/api-keys - paid account needed.)
#
# USE:
#   python gpt_image.py "a 13th-century painted view of Sarai on the Volga, warm light" sarai_painted.png
#   python gpt_image.py --size 1536x1024 "prompt..." out.png
#   python gpt_image.py --edit base.png "make it winter" out.png     (image-to-image edit)
#
# Sizes: 1024x1024, 1536x1024 (landscape), 1024x1536 (portrait). Output PNG.
# Standard library only - no pip installs. Run it on YOUR machine (needs your key + open internet).

import sys, os, json, base64, urllib.request, mimetypes, uuid

def key():
    k = os.environ.get('OPENAI_API_KEY')
    if not k:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openai_key.txt')
        if os.path.exists(p):
            k = open(p).read().strip()
    if not k:
        sys.exit("No API key. Set OPENAI_API_KEY or create openai_key.txt next to this script.")
    return k

def generate(prompt, out, size):
    req = urllib.request.Request(
        'https://api.openai.com/v1/images/generations',
        data=json.dumps({'model': 'gpt-image-1', 'prompt': prompt,
                         'size': size, 'quality': 'high', 'n': 1}).encode(),
        headers={'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    open(out, 'wb').write(base64.b64decode(d['data'][0]['b64_json']))
    print('wrote', out)

def edit(base_img, prompt, out, size):
    boundary = uuid.uuid4().hex
    parts = []
    def field(name, val):
        parts.append(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                      % (boundary, name, val)).encode())
    field('model', 'gpt-image-1'); field('prompt', prompt); field('size', size)
    mt = mimetypes.guess_type(base_img)[0] or 'image/png'
    parts.append(('--%s\r\nContent-Disposition: form-data; name="image"; filename="%s"\r\n'
                  'Content-Type: %s\r\n\r\n' % (boundary, os.path.basename(base_img), mt)).encode())
    parts.append(open(base_img, 'rb').read()); parts.append(b'\r\n')
    parts.append(('--%s--\r\n' % boundary).encode())
    req = urllib.request.Request(
        'https://api.openai.com/v1/images/edits', data=b''.join(parts),
        headers={'Authorization': 'Bearer ' + key(),
                 'Content-Type': 'multipart/form-data; boundary=' + boundary})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.load(r)
    open(out, 'wb').write(base64.b64decode(d['data'][0]['b64_json']))
    print('wrote', out)

if __name__ == '__main__':
    a = sys.argv[1:]
    size = '1536x1024'
    if a and a[0] == '--size': size = a[1]; a = a[2:]
    if a and a[0] == '--edit':
        if len(a) < 4: sys.exit('usage: gpt_image.py --edit base.png "prompt" out.png')
        edit(a[1], a[2], a[3], size)
    elif len(a) >= 2:
        generate(a[0], a[1], size)
    else:
        sys.exit('usage: gpt_image.py [--size WxH] "prompt" out.png   |   --edit base.png "prompt" out.png')
