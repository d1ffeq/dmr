import sys
import imaplib
import getpass
import smtplib
import email
import email.mime.multipart as MIMEMultipart
import email.mime.text as MIMEText
import email.header as Header
from email.header import decode_header




class DialogMailReader:
    def __init__(self):
        self.msg_data = []
        self.known_servers = self.read_serverconfig()


    def read_serverconfig(self):
        f = open('servers.cfg', 'a+').close()
        txt = open('servers.cfg', 'rU').read()
        lines = txt.splitlines()
        line_list = [line for line in lines if line]
        configs = []
        for line in line_list:
            configs.append(line.split('|'))
        return configs


    def write_serverconfig(self, conf_list):
        text = open('servers.cfg', 'w')
        for line in conf_list:
            text.write('{}|{}|{}|{}|{}|{}\n'.format(line[0], line[1], line[2], 
                                                    line[3], line[4], line[5]))
        self.known_servers = self.read_serverconfig()


    def add_server(self):
        new_serv = []
        serv_name = input('Enter service provider name: ')
        address = input('Enter your e-mail account address: ')
        smtp_addr = input('Enter SMTP (SSL) address: ')
        smtp_port = input('Enter SMTP (SSL) port: ')
        imap_addr = input('Enter IMAP (SSL) address: ')
        imap_port = input('Enter IMAP (SSL) port: ')
        if not smtp_port:
            smtp_port = '465'
        if not imap_port: 
            imap_port = '993'
        if serv_name and smtp_addr and imap_addr:
            new_serv.append(serv_name)
            new_serv.append(address)
            new_serv.append(smtp_addr)
            new_serv.append(smtp_port)
            new_serv.append(imap_addr)
            new_serv.append(imap_port)
            if not new_serv in self.known_servers:
                self.known_servers.append(new_serv)
                self.write_serverconfig(self.known_servers)
                self.known_servers = self.read_serverconfig()
                print('\n\nNew server added!\n')


    def decode_msg(self, s):
        if s:
            if s[0:2] == '"=?':
                s = s.replace('"', '')
            s, encoding = decode_header(str(s))[0]
            if encoding:
                s = s.decode(encoding)
            return s
        else: 
            return s


    def server_prompt(self):
        print('\nServers:\n')
        for i in range(0, len(self.known_servers)):
            print('[{}] {} - {}'.format(i + 1, self.known_servers[i][0], self.known_servers[i][1]))
        serv_choice = (int(input('Choose server: ')) - 1)
        if serv_choice < len(self.known_servers):
            acc_data = self.known_servers[serv_choice]
            password = getpass.getpass(prompt = '\nEnter password for {}: '.format(acc_data[1]))
        return acc_data, password


    def fetch_mail(self):
        account, passw = self.server_prompt()
        mailbox = imaplib.IMAP4_SSL(account[4], int(account[5]))
        mailbox.login(account[1], passw)
        selected = mailbox.select('INBOX', readonly = True)
        _, data = mailbox.uid('search', None, 'UNSEEN') 
        msg_uids = data[0].split()
        for id in msg_uids:
            msg = []
            _, reponse = mailbox.uid('fetch', id, '(RFC822)')
            for part in reponse:
                if isinstance(part, tuple):
                    message = email.message_from_bytes(part[1])
                    msg.append(account[1])
                    for h in ('from', 'return-path','date', 'subject'):
                        msg.append(self.decode_msg(message[h]))
                    for m in message.walk():
                        if m.get_content_type() == 'text/plain':
                            body = m.get_payload(decode = True)
                            msg.append(body)
            self.msg_data.append(msg)
        print('\nFetched mail, {} new message(s)\n'.format(len(msg_uids)))
        mailbox.logout()


    def form_message(self):
        new_message = MIMEMultipart.MIMEMultipart()
        new_message['To'] = input('Enter recepient address: ')
        subj = input('Enter subject: ')
        new_message['Subject'] = Header.Header(subj.encode('utf-8'), 'UTF-8').encode()
        print('\nEnter/Paste your message. Ctrl-D (or Ctrl-C) to stop editing.\n')
        msg_lines = []
        while True:
            try:
                line = input('| ')
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            msg_lines.append(line + '\r\n')
        body = ''.join(msg_lines)
        new_message.attach(MIMEText.MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))
        return new_message


    def send_mail(self):
        msg = self.form_message()
        account, passw = self.server_prompt()
        server = smtplib.SMTP_SSL(account[2], int(account[3]))
        server.login(account[1], passw)
        text = msg.as_string()
        server.sendmail(account[1], msg['To'], text)
        server.quit()
        print('\nMessage sent!\n')


    def print_mail(self):
        if self.msg_data:
            for i in range(0, len(self.msg_data)):
                print('\n\n')
                print('To: <{}>'.format(self.msg_data[i][0]))
                print('From: {} <{}>'.format(self.msg_data[i][1], self.msg_data[i][2]))
                print('Date: {}'.format(self.msg_data[i][3]))
                print('Subject: {}'.format(self.msg_data[i][4]))
                print('Message:\n\n{} \n\n'.format((self.msg_data[i][5]).decode('utf-8')))


root = DialogMailReader()
help = '''\nAvailable commands: 
(a)dd account
(f)etch mail
(p)rint all unread mail
(s)end new message
(q)uit\n'''

while(True):
    print(help)
    try:
        command = input('Command: ').upper().rstrip()
        if command == 'A':
            root.add_server()
        elif command == 'F':
            root.fetch_mail()
        elif command == 'P':
            root.print_mail()
        elif command == 'S':
            root.send_mail()
        elif command == 'Q':
            break
        else:
            print('\nUnknown command\n')
    except SystemExit as e:
        pass
    except KeyboardInterrupt:
        break
    except EOFError:
        break
