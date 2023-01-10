import concurrent.futures
import time
import os
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

sec = 5


def client_list():
    sites = pd.read_csv('sites')
    return sites['Site']


def email(site):
    smtp_server = "smtp.gmail.com"
    port = 465
    # context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port) as smtp:
        sender = "sender_email"
        password = 'pwd'
        stamp = time.strftime('%Y-%m-%d, %H:%M:%S')
        smtp.login(sender, password)
        subject = f"{site} {stamp} Outage"
        html = open('mail0.txt', 'r')
        text = html.read()
        html.close()
        receiver = 'receiver_email'
        msg = MIMEMultipart('alternative')

        msg['Subject'] = subject
        msg['From'] = str(Header(f'{site}<{sender}>'))
        msg['To'] = receiver
        part = MIMEText(text, 'html')
        msg.attach(part)
        smtp.sendmail(sender, receiver, msg.as_string())


def serv(site):
    if not os.path.isdir(site):
        os.mkdir(site)
        os.mkdir(f"{site}/target/")
        os.open(os.path.join(site, 'log'), os.O_CREAT)
    elif not os.path.isfile(os.path.join(site, 'log')):
        os.open(os.path.join(site, 'log'), os.O_CREAT)
    elif not os.path.isfile(os.path.join(site, 'count')):
        os.open(os.path.join(site, 'count'), os.O_CREAT)
    elif not os.path.isfile(os.path.join(site, 'up')):
        os.open(os.path.join(site, 'up'), os.O_CREAT)
        u = open(f"{site}/up", 'w')
        u.write('0')
        u.close()
    elif not os.path.isfile(os.path.join(site, 'down')):
        os.open(os.path.join(site, 'down'), os.O_CREAT)
        d = open(f"{site}/down", 'w')
        d.write('0')
        d.close()
    else:
        return


def logs(site):
    time.sleep(sec)
    if os.path.isfile(os.path.join(f'{site}/target/', 'hit')):
        stamp = time.strftime('%Y-%m-%d,%H:%M:%S')
        log = open(f"{site}/log", 'a')
        log.write(f",{stamp},{site},hit \n")
        log.close()
        os.remove(f"{site}/target/hit")
        uf = open(f'{site}/up', 'r+')
        up = int(uf.readline())+sec
        uf.close()
        uf = open(f"{site}/up", "w")
        uf.write(f'{up}')
        uf.close()
        df = open(f"{site}/down", 'r+')
        down_c = int(df.readline())
        df.close()
        if down_c == 0:
            down_c = 0
            down_c += 0
        else:
            count = open(f"{site}/count", 'a')
            count.write(f"{stamp},{site},down,{down_c}\n")
            count.close()
        df = open(f"{site}/down", 'w')
        down = 0
        df.write(f"{down}")
        df.close()
        os.remove(f"{site}/target/hit")
    else:
        stamp = time.strftime('%Y-%m-%d,%H:%M:%S')
        log = open(f"{site}/log", 'a')
        log.write(f",{stamp},{site},miss \n")
        log.close()
        df = open(f"{site}/down", "r+")
        down = int(df.readline())+sec
        df.close()
        df = open(f"{site}/down", "w")
        df.write(f"{down}")
        df.close()
        uf = open(f"{site}/up", 'r+')
        up_c = int(uf.readline())
        uf.close()
        if up_c == 0:
            up_c = 0
            up_c += 0
        else:
            count = open(f"{site}/count", 'a')
            count.write(f"{stamp},{site},up,{up_c} \n")
            count.close()
        uf = open(f"{site}/up", "w")
        up = 0
        uf.write(f"{up}")
        uf.close()


if __name__ == '__main__':
    while True:
        try:
            client_list()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(serv, client_list())
                executor.map(logs, client_list())
            for i in client_list():
                with open(f"{i}/down", "r+") as f:
                    if int(f.readline()) == 900:
                        email(i)

        except Exception as err:
            print(err)
