from requests_html import HTMLSession

import subprocess
import shlex
import sys
import time
import logging
import os
import argparse

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

BASE_URL = 'https://www.wattpad.com'

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

logger = logging.getLogger(__name__)
d = {'clientip': '192.168.0.1', 'user': 'tung491'}


def crawl_all_chaps(link):
    session = HTMLSession()
    r = session.get(link)

    name = r.html.xpath('//span/h1/text()')[0].strip().title()
    author = r.html.xpath('//div[@class="author hidden-lg"]/a[2]/text()')[0]

    urls = r.html.xpath('//ul[@class="table-of-contents"]/li/a/@href')
    links = list(map(lambda x: BASE_URL + x, urls))

    return name, author, links


def crawl_chap(link):
    paragraphs = []

    session = HTMLSession()
    r = session.get(link)

    title = r.html.xpath('//h2/text()')[0].strip()
    page = 1
    logger.info('Crawling chap %s', title, extra=d)

    while True:
        r = session.get(link + '/page/{}'.format(page))
        paragraph = r.html.xpath('//pre//p/text()')
        if paragraph:
            paragraphs.append('<br>'.join(paragraph))
            page += 1
        else:
            break

    content = '<br>'.join(paragraphs)
    logger.info('Crawled chap %s successfully', title.strip(), extra=d)
    return title, content


def generate_html_file(links, name):
    logger.info('Generating HTML file', extra=d)

    content_chaps = []
    html_tpl = """<h2 style="text-align:center;">
                      {}
                  </h2>
                  <br><br>
                  <p>
                    {}
                  </p>
                  <br><br><br>
               """
    for link in links:
        chap_title, chap_content = crawl_chap(link)
        content_chaps.append(html_tpl.format(chap_title, chap_content))

    content = '\n'.join(content_chaps)

    with open('{}.html'.format(name), 'w') as f:
        f.write(content)


def generate_mobi_file(name, author, output_profile):
    cmd_tpl = (
        'ebook-convert "{name}.html" "{name}.mobi" '
        '--output-profile {profile} --level1-toc //h:h2 '
        '--authors "{author}" --title "{name}"'
    )
    logger.info('Generating AZW3 file', extra=d)
    cmd = cmd_tpl.format(name=name, profile=output_profile,
                         author=author)

    subprocess.Popen(shlex.split(cmd))
    time.sleep(10)
    logger.info('Generated AZW3 successfully', extra=d)


def send_email(name):
    from_ = os.getenv('GMAIL_USERNAME')
    to = os.getenv('KINDLE_EMAIL')
    subject = name + '.mobi'

    logger.info('Sending email to %s', to, extra=d)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(from_, os.getenv('GMAIL_PASSWORD'))

    msg = MIMEMultipart()

    msg['From'] = from_
    msg['To'] = to
    msg['Subject'] = subject

    filename = subject
    attachment = open(subject, "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment", filename=filename)
    msg.attach(part)

    text = msg.as_string()
    server.sendmail(from_, to, text)
    server.quit()

    logger.info('Sent email successfully', extra=d)


def upload(name, folder):
    filename = name + '.mobi'

    logger.info('Uploading %s', filename, extra=d)
    if folder:
        cmd = 'gdrive upload -p {} "{}"'.format(folder, filename)
    else:
        cmd = 'gdrive upload {}'.format(filename)
    subprocess.Popen(shlex.split(cmd))

    logger.info('Uploaded %s successfully', filename, extra=d)


def main(url, profile, folder):
    name, author, links = crawl_all_chaps(url)
    if name.find('/') != -1:
        name = name.replace('/', '-')

    generate_html_file(links, name)
    generate_mobi_file(name, author, profile)
    send_email(name)
    upload(name, folder)Công cụ trí tuệ nhân tạo của hãng thương mại điện tử Trung Quốc - Alibaba - có thể tạo ra 20.000 dòng quảng cáo chỉ trong 1 giây.


def cli():
    profiles = ['generic_eink', 'kindle', 'kindle_dx', 'kindle_fire', 'kindle_oasis',
                'kindle_pw', 'kindle_pw3', 'kindle_voyage', 'kobo']

    argp = argparse.ArgumentParser()
    argp.add_argument('url', help='Wattpad link you want generate '
                                  'must starts with https://www.wattpad.com/',
                      type=str)
    argp.add_argument('-f', '--folder', help="Folder ID you want upload into,"
                                             "if not file will upload " 
                                             "into home")
    argp.add_argument('-p', '--profile', help=('Profile you want generate,'
                                              'profiles:' ','.join(profiles) +
                                              'default: Kindle Paperwhite 3'),
                      default='kindle_pw3')
    args = argp.parse_args()

    url = args.url
    profile = args.profile
    folder_id = args.folder

    if not url.startwith(BASE_URL) or not profile in profiles:
        argp.print_help()

    main(url, profile, folder_id)


if __name__ == "__main__":
    cli()