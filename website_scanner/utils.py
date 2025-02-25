import socket
import ssl
import re
import requests
import platform
import os
import dns.resolver
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from colorama import Fore, Style, init
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


init(autoreset=True)

fg = Fore.GREEN
fr = Fore.RED
fw = Fore.WHITE
fy = Fore.YELLOW
fo = Fore.LIGHTYELLOW_EX
flc = Fore.CYAN
bd = Style.BRIGHT
res = Style.RESET_ALL


def print_logo():
    logo_magenta = Fore.MAGENTA
    logo_cyan = Fore.CYAN
    reset = Style.RESET_ALL

    logo = [
        "                                              ",
        "                                              ",
        "                           ─▄▀▀▀▄▄▄▄▄▄▄▀▀▀▄───",
        "                         ───█▒▒░░░░░░░░░▒▒█───",
        "                         ────█░░█░░░░░█░░█────",
        "                         ─▄▄──█░░░▀█▀░░░█──▄▄─",
        "                         █░░█─▀▄░░░░░░░▄▀─█░░█",
        "        @@@@@@@  @@@@@@  @@@@@@@  @@@@@@@ @@@  @@@ @@@@@@@@ @@@@@@@ ",
        "        !@@      @@!  @@@   @@!   !@@      @@!  @@@ @@!      @@!  @@@",
        "        !@!      @!@!@!@!   @!!   !@!      @!@!@!@! @!!!:!   @!@!!@! ",
        "        :!!      !!:  !!!   !!:   :!!      !!:  !!! !!:      !!: :!! ",
        "        :: :: :  :   : :    :     :: :: :  :   : : : :: :::  :   : :",
        "                                                                ",
        "                          @n3ll41 v.0.1                          ",
        "                                                 "
    ]

    for line in logo:
        colored_line = ""
        for char in line:
            if char == '█' or char == '@':
                colored_line += logo_magenta + char
            elif  char == ':' or char == '.':
                colored_line += logo_cyan + char
            else:
                colored_line += reset + char
        print(colored_line + reset)

def get_ip(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except socket.error as e:
        print(f"{fr}[-] Error getting IP address: {e}{fw}")
        return None

def get_cookies(domain):
    os_type = platform.system()
    if os_type == "Windows":
        geckodriver_path = os.path.join(os.path.dirname(__file__), 'geckodriver.exe')
    elif os_type in ["Linux", "Darwin"]:  
        geckodriver_path = os.path.join(os.path.dirname(__file__), 'geckodriver')
    else:
        raise Exception(f"Unsupported OS: {os_type}")
        
    service = FirefoxService(executable_path=geckodriver_path)
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(service=service, options=options)

    cookies = {}
    try:
        driver.get(domain)
        for cookie in driver.get_cookies():
            cookie_name = cookie['name']
            cookies[cookie_name] = cookie['value']
            is_httponly = cookie.get('httpOnly', False)
            is_secure = cookie.get('secure', False)
            samesite = cookie.get('sameSite', 'None')

            print(f"{fg}[+] Cookie: {cookie_name}{fw}")
            if is_httponly:
                print(f"    {fg}HttpOnly: {is_httponly}{fw}")
            else:
                print(f"    {fr}HttpOnly: {is_httponly} - Vulnerable{fw}")

            if is_secure:
                print(f"    {fg}Secure: {is_secure}{fw}")
            else:
                print(f"    {fr}Secure: {is_secure} - Vulnerable{fw}")

            print(f"    SameSite: {samesite}")

    except Exception as e:
        print(f"{fr}[-] Error collecting cookies: {e}{fw}")
    finally:
        driver.quit()
    
    return cookies

def detect_cms(response):
    cms = "Unknown"
    version = "Not detected"
    headers = response.headers
    html = response.text.lower()

    if 'x-powered-by' in headers:
        powered_by = headers['x-powered-by'].lower()
        if 'wordpress' in powered_by:
            cms = 'WordPress'
        elif 'joomla' in powered_by:
            cms = 'Joomla'
        elif 'drupal' in powered_by:
            cms = 'Drupal'
        elif 'typo3' in powered_by:
            cms = 'Typo3'
        elif 'wix' in powered_by:
            cms = 'Wix'
        elif 'magento' in powered_by:
            cms = 'Magento'

    generator_meta = re.search(r'<meta name="generator" content="([^"]+)"', html)
    if generator_meta:
        generator = generator_meta.group(1).lower()
        if 'wordpress' in generator:
            cms = 'WordPress'
            version_search = re.search(r'wordpress (\d+\.\d+(\.\d+)?)', generator)
            if version_search:
                version = version_search.group(1)
        elif 'joomla' in generator:
            cms = 'Joomla'
            version_search = re.search(r'joomla (\d+\.\d+(\.\d+)?)', generator)
            if version_search:
                version = version_search.group(1)
        elif 'drupal' in generator:
            cms = 'Drupal'
            version_search = re.search(r'drupal (\d+\.\d+(\.\d+)?)', generator)
            if version_search:
                version = version_search.group(1)
        elif 'typo3' in generator:
            cms = 'Typo3'
            version_search = re.search(r'typo3 (\d+\.\d+(\.\d+)?)', generator)
            if version_search:
                version = version_search.group(1)
        elif 'wix' in generator:
            cms = 'Wix'
            version_search = re.search(r'wix v(\d+\.\d+(\.\d+)?)', generator)
            if version_search:
                version = version_search.group(1)
        elif 'magento' in generator:
            cms = 'Magento'
            version_search = re.search(r'magento (\d+\.\d+(\.\d+)?)', generator)
            if version_search:
                version = version_search.group(1)

    if cms == "Unknown":
        if 'wp-content' in html or 'wp-includes' in html:
            cms = 'WordPress'
        elif 'joomla' in html:
            cms = 'Joomla'
        elif 'sites/default/files' in html or 'sites/all/modules' in html:
            cms = 'Drupal'
            version_search = re.search(r'drupal-(\d+\.\d+(\.\d+)?)', html)
            if version_search:
                version = version_search.group(1)
        elif 'typo3' in html:
            cms = 'Typo3'
            version_search = re.search(r'typo3 (\d+\.\d+(\.\d+)?)', html)
            if version_search:
                version = version_search.group(1)
        elif 'wix' in html and 'wix-code' in html:
            cms = 'Wix'
            version_search = re.search(r'wix v(\d+\.\d+(\.\d+)?)', html)
            if version_search:
                version = version_search.group(1)
        elif 'mage-' in html or 'magento' in html:
            if re.search(r'magento (\d+\.\d+(\.\d+)?)', html):
                cms = 'Magento'
                version_search = re.search(r'magento (\d+\.\d+(\.\d+)?)', html)
                if version_search:
                    version = version_search.group(1)
            elif 'mage-' in html and 'magento' not in html:
                pass
    
    return cms, version

def get_php_version(headers):
    php_version = "Unknown"
    if 'x-powered-by' in headers:
        php_header = headers['x-powered-by'].lower()
        match = re.search(r'php\/(\d+\.\d+(\.\d+)?)', php_header)
        if match:
            php_version = match.group(1)
    return php_version

def get_webserver_info(headers):
    try:
        server = headers.get('Server', 'Unknown')
        x_powered_by = headers.get('X-Powered-By', 'Unknown')
        if isinstance(server, list):
            server = server[0]
        return server, x_powered_by
    except Exception as e:
        print(f"Could not detect web server information: {e}")
        return 'Unknown', 'Unknown'

def get_os_info(response):
    server = response.headers.get('Server', 'Unknown')
    os_info = 'Unknown'
    if 'nginx' in server.lower():
        os_info = 'Nginx'
    elif 'apache' in server.lower():
        os_info = 'Apache'
    elif 'iis' in server.lower():
        os_info = 'IIS'
    return os_info

def mx_lookup(site):
    try:
        mx_records = dns.resolver.resolve(site, 'MX')
        if not mx_records:
            print(f"{Fore.RED}[-] No MX records found for {site}{Fore.WHITE}")
            return

        mx_record = mx_records[0].exchange.to_text()
        mx_ip = socket.gethostbyname(mx_record)
        mx_hostname = socket.gethostbyaddr(mx_ip)[0]
        mx_result = f"{Fore.GREEN}IP      :{Fore.GREEN} {mx_ip}\n{Fore.GREEN}HOSTNAME:{Fore.WHITE} {mx_hostname}{Fore.WHITE}"
        print(f"{Fore.GREEN}[+] MX Lookup for{Fore.WHITE} {site}")

        print(mx_result)
    except dns.resolver.NoAnswer:
        print(f"{Fore.RED}[-] Error: The DNS response does not contain an answer to the question: {site}. IN MX{Fore.WHITE}")
    except dns.resolver.NXDOMAIN:
        print(f"{Fore.RED}[-] Error: The domain {site} does not exist{Fore.WHITE}")
    except dns.resolver.Timeout:
        print(f"{Fore.RED}[-] Error: Timeout while resolving MX records for {site}{Fore.WHITE}")
    except dns.exception.DNSException as e:
        print(f"{Fore.RED}[-] DNS error: {e}{Fore.WHITE}")
    except socket.gaierror as e:
        print(f"{Fore.RED}[-] Error getting IP address for MX record: {e}{Fore.WHITE}")
    except Exception as e:
        print(f"{Fore.RED}[-] Unexpected error: {e}{Fore.WHITE}")

def check_path(domain, path, headers, cookies):
    url = f"{domain.rstrip('/')}/{path.lstrip('/')}" 
    try:
        response = requests.get(url, headers=headers, cookies=cookies, verify=False, allow_redirects=True, timeout=10)
        if response.status_code == 200:
            print(f"{Fore.GREEN}[+] Found:{Fore.WHITE} {path}")
            if path == "/robots.txt":
                print(f"\n{Fore.GREEN}Contents of robots.txt:{Fore.WHITE}\n{response.text}\n")
            emails = set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text))
            if emails:
                print(f"{Fore.GREEN}[+] Emails found in {path}:{Fore.WHITE}")
                for email in emails:
                    print(f"  - {email}")
        else:
            print(f"{Fore.RED}[-] Path not found: {path}{Fore.WHITE}")
    except requests.exceptions.TooManyRedirects:
        print(f"{Fore.RED}[-] Too many redirects at: {url}{Fore.WHITE}")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[-] Error checking path {path}: {e}{Fore.WHITE}")


def scrape_wordpress_users(domain):
    users_url = domain + "/wp-json/wp/v2/users/"
    try:
        response = requests.get(users_url, verify=False)
        if response.status_code == 200:
            users = response.json()
            if users:
                print(f"\n{fg}[+] WordPress Users:{fw}")
                for user in users:
                    print(f"  - {user['name']} ({user['slug']})")
            else:
                print(f"{fr}[-] No WordPress users found.{fw}")
        else:
            print(f"{fr}[-] Error fetching WordPress users: Status code {response.status_code}{fw}")
    except requests.exceptions.RequestException as e:
        print(f"{fr}[-] Error fetching WordPress users: {e}{fw}")        

def check_plugins_and_themes(domain, cookies):
    try:
        response = requests.get(domain, cookies=cookies, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        plugins = set(re.findall(r'wp-content/plugins/([a-zA-Z0-9_-]+)/', response.text))
        themes = set(re.findall(r'wp-content/themes/([a-zA-Z0-9_-]+)/', response.text))
        if plugins:
            print(f"{Fore.GREEN}[+] Installed Plugins:{Fore.WHITE}")
            for plugin in plugins:
                print(f"  - {plugin}")
        else:
            print(f"{Fore.RED}[-] No plugins found.{Fore.WHITE}")
        if themes:
            print(f"{Fore.GREEN}[+] Installed Themes:{Fore.WHITE}")
            for theme in themes:
                print(f"  - {theme}")
        else:
            print(f"{Fore.RED}[-] No themes found.{Fore.WHITE}")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error checking plugins and themes: {e}{Fore.WHITE}")


def validate_ssl(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                print(f"{Fore.GREEN}[+] SSL/TLS certificate details:{Fore.WHITE}")
                for key, value in cert.items():
                    print(f"  - {key}: {value}")
    except socket.gaierror as e:
        print(f"{Fore.RED}[-] Error validating SSL/TLS certificate: {e}{Fore.WHITE}")
    except Exception as e:
        print(f"{Fore.RED}[-] SSL/TLS validation error: {e}{Fore.WHITE}")

def check_cors(domain):
    try:
        headers = {'Origin': 'http://evil.com'}
        response = requests.get(domain, headers=headers, verify=False)
        if 'Access-Control-Allow-Origin' in response.headers and response.headers['Access-Control-Allow-Origin'] == '*':
            print(f"{fg}[-] CORS vulnerability detected!{fw}")
        else:
            print(f"{fr}[+] No CORS vulnerability detected.{fw}")
    except requests.exceptions.RequestException as e:
        print(f"{fr}Error checking CORS: {e}{fw}")

def check_security_txt(domain):
    check_path(domain, "/.well-known/security.txt", {}, {})

def check_captcha(domain, headers, cookies):
    try:
        response = requests.get(domain, headers=headers, cookies=cookies, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        forms = soup.find_all('form')
        found_captcha = False
        found_cloudflare = False

        for form in forms:
            if 'captcha' in str(form).lower():
                print(f"{fg}[+] Captcha found in form{fw}")
                found_captcha = True
                break
        if not found_captcha:
            print(f"{fr}[-] No Captcha found in forms{fw}")

        if 'cf-challenge' in response.text.lower() or 'cloudflare' in response.text.lower():
            print(f"{fg}[+] Cloudflare protection detected{fw}")
            found_cloudflare = True
        if not found_cloudflare:
            print(f"{fr}[-] No Cloudflare protection detected{fw}")

    except requests.exceptions.RequestException as e:
        print(f"{fr}[-] Error checking for Captcha or Cloudflare: {e}{fw}")
