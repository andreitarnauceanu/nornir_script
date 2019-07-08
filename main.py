from nornir import InitNornir
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.tasks.text import template_file
from nornir.plugins.tasks.networking import napalm_configure, netmiko_send_command
from nornir.plugins.functions.text import print_result
import subprocess as sp


def load_isp_data(task):
    data = task.run(
        task=load_yaml,
        file=f'groups/nornir_network.yaml'
    )
    run_task(data, 'isp_router.j2', task)


def load_ce_data(task):
    data = task.run(
        task=load_yaml,
        file=f'groups/ce_routers.yaml'
    )
    run_task(data, 'ce_router.j2', task)



def erase_config_and_reboot(task):
    task.run(
        netmiko_send_command,
        command_string="\x03\n\nwrite erase\n",
        enable=True)
    task.run(
        netmiko_send_command,
        command_string='reload\n\nn\n',
        enable=True,
        expect_string="")

def limit_logging_console(task):
    task.run(
        netmiko_send_command,
        command_string="\x03\nenable\nconf term\nlogging console 0\nend\n",
        enable=True)


def run_task(data, template, task):
    for key in data.result.keys():
        task.host[key] = data.result[key]
    response = task.run(task=template_file, template=template, path="templates")
    task.host["template_config"] = response.result
    task.run(task=napalm_configure, replace=False, configuration=task.host["template_config"])


nornir = InitNornir(config_file="config.yaml")

while True:
    tmp = sp.call('clear', shell=True)
    print("0. Limit logging output")
    print("1. Configure ISP routers")
    print("2. Configure CE routers")
    print("3. Erase configuration and reboot")
    option = input('Option: ')

    if option == '0':
        print("Limiting logging output...")
        r = nornir.run(limit_logging_console)
        print_result(r)
    elif option == '1':
        print("Configuring ISP routers...")
        isp = nornir.filter(site='nornir')
        r = isp.run(load_isp_data)
        print_result(r)
    elif option == '2':
        print("Configuring CE routers...")
        clients = nornir.filter(site='clients')
        r = clients.run(load_ce_data)
        print_result(r)
    elif option == '3':
        print("Erasing configuration...")
        clear = nornir.run(erase_config_and_reboot)
        print_result(clear)
    elif option == 'q':
        break
    input('Press any enter to continue...')
