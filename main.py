from nornir import InitNornir
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.tasks.text import template_file
from nornir.plugins.tasks.networking import napalm_configure, netmiko_save_config, netmiko_send_command
from nornir.plugins.functions.text import print_result


def load_data(task):
    data = task.run(
           task=load_yaml,
           file=f'{task.host.groups[0]}.yaml'
    )
    for key in data.result.keys():
        task.host[key] = data.result[key]
    r = task.run(task=template_file, template="router.j2", path="templates")
    task.host["template_config"] = r.result
    task.run(task=napalm_configure, replace=False, configuration=task.host["template_config"])


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


def no_logging_monitor(task):
    task.run(
        netmiko_send_command,
        command_string="\x03\n\nconf term\nno logging monitor\nend\n",
        enable=True)


nr = InitNornir(config_file="config.yaml")
nornir = nr.filter(site="nornir")

print("1. Configure network")
print("2. Erase configuration and reboot")

option = input('Option: ')

if option == '1':
    r = nornir.run(no_logging_monitor)
    print_result(r)
    r = nornir.run(load_data)
    print_result(r)
elif option =='2':
    clear = nornir.run(erase_config_and_reboot)
    print_result(clear)


