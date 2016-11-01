import pika
import sys
import os
import subprocess
import json
##get project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from django.core.wsgi import get_wsgi_application
##get project parent directory and add to python path using sys.path.append
SYS_PATH = os.path.dirname(BASE_DIR)
print SYS_PATH
if SYS_PATH not in sys.path:
    sys.path.append(SYS_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = 'Caas.settings'
application = get_wsgi_application()
from ccloud.models import Container
from ccloud.models import RequestQueue
from io import BytesIO
from docker import Client
import docker.tls as tls

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='reqqueue')

def create_container(cname,user,giturl):
    try:
        error = False
        errmsg = ''
        cid=''
        host_port=''
        print('nodeJsBuild start');    
        print('file creation')
        cli = Client(base_url='unix://var/run/docker.sock')
        #tls_config = tls.TLSConfig(  
        #    client_cert=('/Users/kasi-mac/.docker/machine/machines/default/cert.pem', '/Users/kasi-mac/.docker/machine/machines/default/key.pem'),
        #    ca_cert='/Users/kasi-mac/.docker/machine/machines/default/ca.pem', verify=True)
        #cli = Client(base_url='tcp://192.168.99.100:2376', tls=tls_config)
        print('cli creation')
        response = [line for line in cli.build(path=giturl, rm=True, tag=user+'/'+cname)]
        print(response)
        print('cli creation end')
        container = cli.create_container(image=user+'/'+cname,name=cname,host_config=cli.create_host_config(publish_all_ports= True))
        print(container)
        ccrres = json.loads(json.dumps(container))
        if 'Id' not in ccrres:
            error = True
            errmsg = 'Container creation failed'
        else:
            print('1')
            cid = ccrres['Id']
            print(cid)
            response = cli.start(container=container.get('Id'))
            print(response)    
            if response != None:            
                error = True
                errmsg = 'Container failed to start'
            else:       
                error = False
                info = cli.inspect_container(container)
                print info
                host_port = 'http://'+str(info['NetworkSettings']['Ports']['8080/tcp'][0]['HostIp'])+':'+str(info['NetworkSettings']['Ports']['8080/tcp'][0]['HostPort'])
		print host_port
        return error,errmsg,cid,host_port
    except Exception as inst:
	print inst.args
        return True,'Exception','',''

def remove_container(id):
    cli = Client(base_url='unix://var/run/docker.sock')
    try:
        cli.remove_container(id,force='true')
        return True
    except:
        return False
    
def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    rq = RequestQueue.objects.get(id=body)
    c = rq.container_id
    print(c.devstack_container_id)
    if c.container_or_service==Container.CONTAINER:
        if c.status == Container.STATUS_FORCREATE:
            error,errmsg,id,url = create_container(c.container_name,c.user_id.username,c.git_url)
            if error == False:
                c.status=Container.STATUS_CREATED
                c.devstack_container_id=id
                c.container_url=url
                c.save()
            else:
                c.status=Container.STATUS_CREATE_FAILED
                c.save()
        elif c.status == Container.STATUS_FORMODIFY:
            error = remove_container(c.devstack_container_id)
            print error
            if error == False:
                print 'errr'
                c.status=Container.STATUS_MODIFY_FAILED
            else:
                print 'else'            
                error,errmsg,id,url = create_container(c.container_name,c.user_id.username,c.git_url)
                if error == False:
                    print 'mod'
                    c.status=Container.STATUS_MODIFIED
                    c.devstack_container_id=id
                    c.container_url=url
                    c.save()
                else:          
                    print 'else11'
                    c.status=Container.STATUS_MODIFY_FAILED
                    c.save()
        elif c.status == Container.STATUS_FORDELETE:
            print(str(c.devstack_container_id))
            error = remove_container(str(c.devstack_container_id))
            if error == False:
                c.status=Container.STATUS_DELETE_FAILED
            else:
                c.status=Container.STATUS_DELETED
            c.save()
    else:
        if c.status == Container.STATUS_FORCREATE:
            output = subprocess.check_output(['./script/CreateService.sh',str(c.cluster_id.master_name),str(c.cluster_id.master_ip),str(c.container_name),str(c.user_id.username),str(c.git_url),str(c.port)])
            print output
        elif c.status == Container.STATUS_FORMODIFY:
            output = subprocess.check_output(['./script/scaleService.sh',str(c.cluster_id.master_name),str(c.cluster_id.master_ip),str(c.container_name),str(c.scale)])
            print output            
        elif c.status == Container.STATUS_FORDELETE:    
            output = subprocess.check_output(['./script/removeService.sh',str(c.cluster_id.master_name),str(c.cluster_id.master_ip),str(c.container_name)])
            print output
         
channel.basic_consume(callback,
                      queue='reqqueue',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
