from enmutils_int.lib.nrm_default_configurations import basic_network
from enmutils_int.lib.nrm_default_configurations import soem_five_network
from enmutils_int.lib.nrm_default_configurations import five_network
from enmutils_int.lib.nrm_default_configurations import forty_network
from enmutils_int.lib.nrm_default_configurations import sixty_network
from enmutils_int.lib.nrm_default_configurations import fifteen_network
from enmutils_int.lib.nrm_default_configurations import extra_small_network
from enmutils_int.lib.nrm_default_configurations import one_hundred_network
from enmutils_int.lib.nrm_default_configurations import transport_twenty_network
from enmutils_int.lib.nrm_default_configurations import transport_ten_network

networks = dict(basic_network.basic.items() + sixty_network.sixty_k_network.items() +
                five_network.five_k_network.items() + forty_network.forty_k_network.items() +
                fifteen_network.fifteen_k_network.items() + one_hundred_network.one_hundred_k_network.items() +
                soem_five_network.soem_five_k_network.items() + extra_small_network.extra_small_network.items() +
                transport_twenty_network.transport_twenty_k_network.items() +
                transport_ten_network.transport_ten_k_network.items())
