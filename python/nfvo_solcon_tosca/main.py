# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.dp import Action
import ncs.maapi as maapi
import sys
import json
import yaml
if sys.version_info >= (3, 0):
    from . import simple_profile_for_nfv as sp
    import urllib.request as ul
else:
    import urllib as ul
    import simple_profile_for_nfv as sp


class ImportAction(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output):
        log.info('action input: ', input.uri)

        if input.raw:
            tosca = input.raw
        else:
            tosca = self._load_uri(input.uri)

        log.debug("TOSCA = {}".format(tosca))

        tosca_vnf = yaml.load(tosca)

        vnfd = sp.tosca2cvnfd(tosca_vnf)
        log.debug("VNFD = {}".format(vnfd))

        # Wrap vnfd in /nfvo/vnfd
        vnfd = {
            "tailf-etsi-rel2-nfvo:nfvo": {
                "vnfd": vnfd
            }
        }

        with maapi.single_write_trans(uinfo.username, "tailf-etsi-rel2-nfvo-tosca") as th:
            # vnfds = maagic.get_root(th).nfvo.vnfd
            log.info("JSON: {}".format(json.dumps(vnfd)))
            th.load_config_cmds(maapi.CONFIG_JSON | maapi.CONFIG_MERGE, json.dumps(vnfd), "/nfvo/vnfd")

            th.apply()

    def _load_uri(self, uri):
        f = ul.urlopen(uri)
        return f.read()


class Main(ncs.application.Application):
    def setup(self):
        self.register_action('tailf-etsi-rel2-nfvo-tosca-import', ImportAction)

    def teardown(self):
        pass
