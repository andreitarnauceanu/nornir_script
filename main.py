from nornir import InitNornir
from nornir.plugins.tasks.data import load_yaml
from nornir.plugins.tasks.text import template_file
from nornir.plugins.tasks.networking import napalm_configure, netmiko_save_config, netmiko_send_command
from nornir.plugins.functions.text import print_result
from yaml import dump


def load_data(task):
    data = task.run(
        task=load_yaml,
        file=f'groups/nornir_network.yaml'
    )
    run_task(data, 'router.j2', task)


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


def populate_group_files(nr):
    groups = ['pe', 'reflector']
    for group in groups:
        mbgp_filter = nr.filter(mbgp_type=group)
        hosts = mbgp_filter.inventory.hosts
        neighbors = [host['loopback0'] for host in hosts.values()]
        if group == 'pe':
            filename = 'groups/reflector_routers.yaml'
        else:
            filename = 'groups/pe_routers.yaml'
        with open(filename, 'w') as f:
            data = '# this file is generated automaticly\n'
            data = data + dump({'neighbors': neighbors})
            f.write(data)


def mbgp_configure_reflector(task):
    data = task.run(
        task=load_yaml,
        file=f'groups/reflector_routers.yaml'
    )
    run_task(data, 'mbgp.j2', task)


def mbgp_configure_pe(task):
    data = task.run(
        task=load_yaml,
        file=f'groups/pe_routers.yaml'
    )
    run_task(data, 'mbgp.j2', task)


def run_task(data, template, task):
    for key in data.result.keys():
        task.host[key] = data.result[key]
    r = task.run(task=template_file, template=template, path="templates")
    task.host["template_config"] = r.result
    task.run(task=napalm_configure, replace=False, configuration=task.host["template_config"])


nr = InitNornir(config_file="config.yaml")

print("1. Configure network")
print("2. Erase configuration and reboot")
print("3. Configure mbgp")
option = input('Option: ')



if option == '1':
    nornir = nr.filter(site="nornir")
    r = nornir.run(limit_logging_console)
    print_result(r)
    r = nornir.run(load_data)
    print_result(r)
elif option =='2':
    clear = nr.run(erase_config_and_reboot)
    print_result(clear)
elif option=='3':
    populate_group_files(nr)
    mbgp_pe_hosts = nr.filter(mbgp_type='pe')
    result = mbgp_pe_hosts.run(mbgp_configure_pe)
    print_result(result)
    mbgp_reflector_hosts = nr.filter(mbgp_type='reflector')
    result = mbgp_reflector_hosts.run(mbgp_configure_reflector)
    print_result(result)