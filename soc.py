import configparser, requests, jxmlease, os
import base64, zipfile, json, mysql.connector
from lxml import etree
import xml.etree.ElementTree as ET
from datetime import datetime


def sql_query(cursor,query,text):
    cursor.execute(query % text)
    query_result = cursor.fetchall()
    return(query_result)

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'settings.ini'))

login = config['rkn']['login']
password = config['rkn']['password']
path = config['system']['path']
unzip_path = config['system']['unzip_path']
DB = config['mysql']['DB']
DB_uname = config['mysql']['username']
DB_pass = config['mysql']['password']
DB_host = config['mysql']['host']
DB_port = config['mysql']['port']

mysql_config = {'user': DB_uname,
                'password': DB_pass,
                'host': DB_host,
                'port': DB_port,
                'database': DB}

download_url = 'https://vigruzki2.rkn.gov.ru/services/OperatorRequest2/'

headers = {'Content-Type':'text/xml'}

body="""<soap:Envelope soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
               xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:tns="http://vigruzki.rkn.gov.ru/OperatorRequest/">
    <soap:Body>
	<tns:getResultSocResources>
	    <code xsi:type="xsd:string\">
	    </code>
	</tns:getResultSocResources>
    </soap:Body>
</soap:Envelope>
"""

try:
    r = requests.post(download_url, data=body, headers=headers,
                      auth=(login,
                            password),
                      timeout = 300)
except Exception as e:
    print(e)

root = jxmlease.parse(r.content)
zip_file = base64.b64decode(root['SOAP-ENV:Envelope']['SOAP-ENV:Body']['ns1:getResultResponse']['registerZipArchive'])

with open(path,'wb') as f:
    f.write(zip_file)

with zipfile.ZipFile(path,'r') as rkn_zip:
    rkn_zip.extractall(unzip_path)

tree = ET.parse(str(unzip_path) + 'register.xml')

root = tree.getroot()

list_update_time = root.attrib['updateTime']

head, sep, tail = list_update_time.partition('+')

rkn_date = datetime.strptime(head, '%Y-%m-%dT%H:%M:%S')

try:
    mysql_connect = mysql.connector.connect(**mysql_config)
    cursor = mysql_connect.cursor()

    query = "select list_date from update_info where id='%s'"
    list_update_db = sql_query(cursor, query, '1')


    if list_update_db[0][0] < rkn_date:
        query = "update update_info set list_date= %s where id=1;"
        cursor.execute(query,(rkn_date,))
        mysql_connect.commit()
        
        for child in root:
            if child.tag == 'content':
                domain_id = child.attrib['id']
                domain_add_time = child.attrib['includeTime']
                head, sep, tail = domain_add_time.partition('+')
                domain_add_t = datetime.strptime(head, '%Y-%m-%dT%H:%M:%S')
                for content in child:
                    if content.tag == 'resourceName':
                        domain_descr = content.text

                    if content.tag == 'domain':
                        domain_name = content.text
                        query = "insert IGNORE into domains(id,domain,descr,domain_add_time) values(%s,%s,%s,%s);"
                        cursor.execute(query,(domain_id,domain_name,domain_descr,domain_add_t))
                        mysql_connect.commit()

                    if content.tag == 'ipSubnet':
                        ip_subnet = content.text
                        query = "insert IGNORE into ip_subnets(domain_id,subnet) values(%s,%s);"
                        cursor.execute(query,(domain_id,ip_subnet))
                        mysql_connect.commit()

finally:
    mysql_connect.close()
