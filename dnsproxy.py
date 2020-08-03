#!/usr/bin/env python3

import socket
import sys
import struct
import _thread
import codecs
import ipaddress
import re
import os
from optparse import OptionParser
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
try:
    import dpkt
except:
    print('Please install dpkd using pip') #Призываем установить библиотеку dpkd

try:
    from dnslib import *
except:
    print('Please install dnslib using pip') #Призываем установить библиотеку dnslib


class DNSProxy:
    
    BLACK_LIST = {}

    local_port = 53
    local_host = '0.0.0.0' #Будем слушать на всех интерфейсах
    remote_dns_ip = ''
    
    # Проверяет является ли строка ip-адресом
    def is_ip_addr(self, s):
        return re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', s)

    # Конвертирует UDP DNS запрос в TCP DNS запрос
    def convertRequestToTcp(self, request):
        return b"\x00"+ bytes(chr(len(request)),'utf-8') + bytes(request)

    # Посылает TCP DNS запрос к вышестоящему DNS-серверу
    def sendRequest(self, request):
        remote = (self.remote_dns_ip, 53)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(remote)
        request = self.convertRequestToTcp(request)
        sock.sendto(bytes(request), ( self.remote_dns_ip, 53) )
        response = sock.recv(1024)
        return response[2:]

    # Создает DNS ответ для позиций из Black List
    def buildResponse(self, request):
        dns = DNSRecord.parse(request)

        qname = str(dns.q.qname)
        qtype = QTYPE[dns.q.qtype]

        rule = self.searchInBlackList(dpkt.dns.DNS(request).qd[0].name)
        
        is_ip = self.is_ip_addr(rule)

        if is_ip:
            response = DNSRecord(DNSHeader(id=dns.header.id, bitmap=dns.header.bitmap, qr=1, aa=1, ra=1, rcode=0), q=dns.q)
            response.add_answer(RR(qname, getattr(QTYPE,qtype), rdata=RDMAP[qtype](str(rule))))
        else:
            response = DNSRecord(DNSHeader(id=dns.header.id, bitmap=dns.header.bitmap, qr=1, aa=1, ra=1, rcode=3), q=dns.q)
            response.add_auth(RR("dnsproxy",QTYPE.SOA,ttl=60,rdata=SOA("ns.dnsproxy","admin.dnsproxy",(20140101,10800,3600,604800,38400))))

        return response.pack()
        


    # Отправляет UDP DNS ответ клиенту
    def sendAnswer(self, addr, sock, data):
        sock.sendto(bytes(data), addr)

    # Ищет соответствие в Black List, если есть, возвращает правило
    def searchInBlackList(self, h):
        for host in self.BLACK_LIST:
            if host[:2] == '*.':
                ptr = '.*' + host.replace('*.', '').replace('.', '\.') + '$'
            else:
                ptr = host.replace('.', '\.')
            res = re.match(ptr, h)
            if res:
                return self.BLACK_LIST[host]

    # Обрабатывает UDP запрос. Проверяет есть ли доменное имя в черном списке и выбирает способ генерации ответа (TCP запрос к upstream DNS или создание своего ответа)
    def handler(self, data, addr, sock):
        request = dpkt.dns.DNS(data)
        host_name = request.qd[0].name
        host_name = self.searchInBlackList(host_name)
        
        if host_name is not None:
            response = self.buildResponse(data)
        else:
            response = self.sendRequest(request)

        if self.verify_request(request) is not True:
            print("Запрос не соответсвует DNS запросу. Ошибка протокола!")
            #return
        self.sendAnswer(addr, sock, response)


    # Проверяет корректность DNS запроса (возможно требуется доработка)
    def verify_request(self, request):
        if request.qr != dpkt.dns.DNS_Q:
            return False
        if request.opcode != dpkt.dns.DNS_QUERY:
            return False
        if len(request.qd) != 1:
            return False
        if len(request.an) != 0:
            return False
        if len(request.ns) != 0:
            return False
        if request.qd[0].cls != dpkt.dns.DNS_IN:
            return False
        if request.qd[0].type != dpkt.dns.DNS_A:
            return False
        return True

    # Считывает файл конфигурации, устанавливает Upstream DNS Server и Black List
    def parseSettings(self, path):

        if not os.path.exists(path):
            print("Ошибка. Файл настроек '" + path + "' не существует. \n")
            exit(-1)
        
        try:
            config = configparser.ConfigParser()
            config.read(path)
        except Exception as e:
            print(e)
            exit(0)
        
        try:
            self.remote_dns_ip = config.get("DNS Server", "ip")
        except Exception as e:
            print(e)
        black_list = config._sections['Black List']
        for item in black_list:
            try:
                if item == '__name__': continue
                self.BLACK_LIST[item] = config._sections['Black List'][item]
            except Exception as e:
                print(e)
                continue

    # Слушает UDP порт и запускает обработчик в новом потоке
    def __init__(self, config, port):
        
        self.parseSettings(config)
        self.local_port = port

        try:
            # Настраиваем UDP сервер для приема UDP DNS запросов
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self.local_host, self.local_port))
            while True:
                data, addr = sock.recvfrom(1024)
                #self.handler(data, addr, sock)
                _thread.start_new_thread(self.handler, (data, addr, sock))
        except Exception as e:
            print(e)
            sock.close()
        
# Разбирает опции командной строки, запускает экземпляр класса DNSProxy
if __name__ == '__main__':
    
    parser = OptionParser(usage = "dnsproxy.py [options]", description="Приложение требует права root для запуска на привилегированных портах." )
    parser.add_option("-p","--port", dest="port", metavar="", default=53, help="Номер порта для приема DNS запросов. 53 по умолчанию")
    parser.add_option("-c","--config", dest="config", metavar="", default="settings.conf", help="Пусть к файлу настроек (settings.ini по умолчанию)")
    (options,args) = parser.parse_args()
    
    if not options.config:
        parser.print_help()
        exit(0)
    
    config = options.config
    port = int(options.port)
    
    try:
        DNSProxy(config, port)
    except Exception as e:
        print(e)
