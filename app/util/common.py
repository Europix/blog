from flask import request,current_app, url_for
from flask import abort
from flask_login import current_user
from functools import wraps
import requests
import json
import re
import uuid
import os
from html2text import HTML2Text
from bs4 import BeautifulSoup
from urllib import parse
from datetime import datetime


def admin_required(func):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_admin():
                abort(403)
                # If user is not an admin:
            return f(*args, **kwargs)
        return decorated_function
    return decorator(func)


def author_required(func):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_author():
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator(func)


def isAjax() -> bool :
    ajax_header = request.headers.get('X-Requested-With')
    if ajax_header and ajax_header == 'XMLHttpRequest':
        return True
    return False


def pretty_date(time=False):
    # Transfer datetime to a pretty date.
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['Europix_ALLOWED_IMAGE_EXTENSIONS']


def strip_tags(string, allowed_tags=''):
    if allowed_tags != '':
        # Get a list of all allowed tag names.
        allowed_tags = allowed_tags.split(',')
        allowed_tags_pattern = ['</?'+allowed_tag+'[^>]*>' for allowed_tag in allowed_tags]
        all_tags = re.findall(r'<[^>]+>', string, re.I)
        not_allowed_tags = []
        tmp = 0
        for tag in all_tags:
            for pattern in allowed_tags_pattern:
                rs = re.match(pattern,tag)
                if rs:
                    tmp += 1
                else:
                    tmp += 0
            if not tmp:
                not_allowed_tags.append(tag)
            tmp = 0
        for not_allowed_tag in not_allowed_tags:
            string = re.sub(re.escape(not_allowed_tag), '',string)
        print(not_allowed_tags)
    else:
        # If no allowed tags, remove all.
        string = re.sub(r'<[^>]*?>', '', string)
  
    return string


def get_bing_img_url(format='js',idx=0):
    url = 'https://cn.bing.com/HPImageArchive.aspx?format={}&idx={}&n=1'.format(format,idx)
    resp = requests.get(url,timeout=5).text
    data = json.loads(resp)
    return 'https://cn.bing.com{}'.format(data['images'][0]['url'])


def get_short_id() -> str:
    array = [ "0", "1", "2", "3", "4", "5","6", "7", "8", "9",
          "a", "b", "c", "d", "e", "f","g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s","t", "u", "v", "w", "x", "y", "z",
          "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
          ]
    id = str(uuid.uuid4()).replace("-", '')
    buffer = []
    for i in range(0, 8):
        start = i *  4
        end = i * 4 + 4
        val = int(id[start:end], 16)
        buffer.append(array[val % 62]) 
    return "".join(buffer)


def strdecode(text):
    if not isinstance(text, str):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            text = text.decode('gbk', 'ignore')
        return text
    return text


def open_url(url):
    header = {
        'User-Agent':'Mozilla/5.0 (Windows NT 6.2; rv:16.0) Gecko/20100101 Firefox/16.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection':'keep-alive'
    }
    html = requests.get(url, headers = header).text
    return html


def full_url(url, src):
    src_parse = parse.urlparse(src)
    if not src_parse.netloc and not src_parse.scheme:
        if not src.startswith("/"):
            end_index = url.rfind("/")
            url = url[:end_index]
            src = u"{0}/{1}".format(url, src)
        else:
            url = parse.urlparse(url)
            src = u"{0}://{1}{2}".format(url.scheme, url.netloc, src)
    elif not src_parse.scheme:
        url = parse.urlparse(url)
        src = u"{0}:{1}".format(url.scheme, src)
    return src


def download_file(url, filename):
    url_path = ''
    try:
        req = requests.get(url, stream=True, timeout=3)

    except:
        return False
    if req.status_code == 200:
        upload_type = current_app.config.get('Europix_UPLOAD_TYPE')
        if upload_type is None or upload_type == '' or upload_type == 'local':
            with open(os.path.join(current_app.config['Europix_UPLOAD_PATH'], filename)) as f:
                f.write(req.content)
            url_path = url_for('admin.get_image', filename=filename)
    return url_path


def download_html_image(url, html, path):
    soup = BeautifulSoup(html, "html.parser")
    imgs = soup.select("img")
    for img in imgs:
        if not img.has_attr("src"):
            continue
        src = img['src'] if not url else full_url(url, img["src"])
        _, ext = os.path.splitext(src)
        filename = datetime.now().strftime('%Y%m%d%H%M%S')+ext
        img_new_url = download_file(src, filename)
        if img_new_url != '':
            img['src'] = img_new_url
    return str(soup)


def html_remove_all_a(html)-> str:
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all('a'):
        if a.string:
            a.replace_with(a.string)
    return str(soup)


def html2markdown(html, url, download, path):
    html = html_remove_all_a(html)
    if not download:
        h = HTML2Text(baseurl = url, bodywidth = 0)
    else:
        html = download_html_image(url, html, path)
        h = HTML2Text(bodywidth = 0)
    md = h.handle(html)
    return md


if __name__ == "__main__":
    codes = 1
    print(codes)
