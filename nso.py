import requests
import logging

log = logging.getLogger(__name__)

baseUrl = 'http://localhost:8080/restconf/data/nfvo'
headers = {
    'Accept': 'application/yang-data+json',
    'Content-Type': 'application/yang-data+json'
}
auth = ('admin', 'admin')


def store(vnfd):
    vnfid = vnfd['id']
    payload = {
        'tailf-etsi-rel2-nfvo:vnfd': vnfd
    }
    log.info("storing vnfd {}".format(vnfid))
    r = requests.put(baseUrl + "/vnfd=" + vnfid,
                     headers=headers,
                     auth=auth,
                     json=payload)
    log.info("requests response: {}".format(r.text))
