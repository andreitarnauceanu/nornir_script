from nornir import InitNornir
from nornir.plugins.tasks.networking import napalm_get
from nornir.plugins.functions.text import print_result

nr = InitNornir(config_file="config.yaml")
#import pdb; pdb.set_trace()
result = nr.run(
             napalm_get,
             getters=['get_facts'])

print_result(result)
